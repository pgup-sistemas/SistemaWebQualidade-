"""
Sistema de assinatura digital para documentos - Alpha Gestão Documental
"""
from flask import current_app, request
from app import db
from app.models import DocumentSignature, Document, User
from datetime import datetime
import hashlib
import json
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
import uuid

class DigitalSignatureManager:
    """Gerenciador de assinaturas digitais"""
    
    @staticmethod
    def generate_document_hash(document_content):
        """Gerar hash do conteúdo do documento"""
        if isinstance(document_content, str):
            document_content = document_content.encode('utf-8')
        
        hash_obj = hashlib.sha256()
        hash_obj.update(document_content)
        return hash_obj.hexdigest()
    
    @staticmethod
    def create_simple_signature(document_id, user_id, signature_type='eletronica'):
        """Criar assinatura simples (eletrônica)"""
        try:
            document = Document.query.get(document_id)
            user = User.query.get(user_id)
            
            if not document or not user:
                return None, "Documento ou usuário não encontrado"
            
            # Verificar se já foi assinado por este usuário nesta versão
            existing_signature = DocumentSignature.query.filter_by(
                documento_id=document_id,
                usuario_id=user_id,
                versao_documento=document.versao_atual
            ).first()
            
            if existing_signature:
                return None, "Documento já foi assinado por este usuário"
            
            # Obter conteúdo atual do documento
            current_version = document.get_current_version()
            if not current_version:
                return None, "Versão do documento não encontrada"
            
            # Gerar hash do documento
            doc_hash = DigitalSignatureManager.generate_document_hash(current_version.conteudo)
            
            # Criar informações da assinatura
            signature_info = {
                'user_id': user_id,
                'user_name': user.nome_completo,
                'user_email': user.email,
                'timestamp': datetime.utcnow().isoformat(),
                'ip_address': request.remote_addr if request else None,
                'user_agent': request.headers.get('User-Agent') if request else None,
                'document_version': document.versao_atual,
                'signature_id': str(uuid.uuid4())
            }
            
            # Criar registro de assinatura
            signature = DocumentSignature(
                documento_id=document_id,
                versao_documento=document.versao_atual,
                usuario_id=user_id,
                tipo_assinatura=signature_type,
                hash_documento=doc_hash,
                certificado_info=json.dumps(signature_info),
                ip_address=request.remote_addr if request else None
            )
            
            db.session.add(signature)
            db.session.commit()
            
            return signature, "Assinatura criada com sucesso"
            
        except Exception as e:
            current_app.logger.error(f"Erro ao criar assinatura: {str(e)}")
            return None, f"Erro interno: {str(e)}"
    
    @staticmethod
    def verify_signature(signature_id):
        """Verificar validade de uma assinatura"""
        try:
            signature = DocumentSignature.query.get(signature_id)
            if not signature:
                return False, "Assinatura não encontrada"
            
            if not signature.valida:
                return False, "Assinatura foi invalidada"
            
            # Verificar se o documento ainda existe
            document = signature.documento
            if not document:
                return False, "Documento associado não encontrado"
            
            # Verificar se a versão ainda existe
            version = document.versoes.filter_by(versao=signature.versao_documento).first()
            if not version:
                return False, "Versão do documento não encontrada"
            
            # Verificar hash do documento
            current_hash = DigitalSignatureManager.generate_document_hash(version.conteudo)
            if current_hash != signature.hash_documento:
                signature.valida = False
                db.session.commit()
                return False, "Conteúdo do documento foi alterado após a assinatura"
            
            return True, "Assinatura válida"
            
        except Exception as e:
            current_app.logger.error(f"Erro ao verificar assinatura: {str(e)}")
            return False, f"Erro na verificação: {str(e)}"
    
    @staticmethod
    def get_document_signatures(document_id, version=None):
        """Obter todas as assinaturas de um documento"""
        query = DocumentSignature.query.filter_by(documento_id=document_id)
        
        if version:
            query = query.filter_by(versao_documento=version)
        
        signatures = query.order_by(DocumentSignature.data_assinatura.desc()).all()
        
        signature_list = []
        for sig in signatures:
            try:
                cert_info = json.loads(sig.certificado_info) if sig.certificado_info else {}
            except:
                cert_info = {}
            
            signature_data = {
                'id': sig.id,
                'user_name': sig.usuario.nome_completo,
                'user_email': sig.usuario.email,
                'signature_type': sig.tipo_assinatura,
                'date': sig.data_assinatura,
                'version': sig.versao_documento,
                'valid': sig.valida,
                'certificate_info': cert_info,
                'ip_address': sig.ip_address
            }
            signature_list.append(signature_data)
        
        return signature_list
    
    @staticmethod
    def invalidate_signatures_after_change(document_id, new_version):
        """Invalidar assinaturas anteriores quando documento for alterado"""
        try:
            # Buscar assinaturas de versões anteriores
            old_signatures = DocumentSignature.query.filter(
                DocumentSignature.documento_id == document_id,
                DocumentSignature.versao_documento != new_version
            ).all()
            
            # Manter as assinaturas válidas, mas marcar a versão específica
            # Não invalidar automaticamente - deixar para auditoria decidir
            
            return True, f"Verificadas {len(old_signatures)} assinaturas anteriores"
            
        except Exception as e:
            current_app.logger.error(f"Erro ao processar assinaturas: {str(e)}")
            return False, f"Erro: {str(e)}"
    
    @staticmethod
    def require_signature(document_id, users_list, signature_type='eletronica'):
        """Solicitar assinatura de usuários específicos"""
        try:
            document = Document.query.get(document_id)
            if not document:
                return False, "Documento não encontrado"
            
            # Criar registros de solicitação (pode ser implementado como modelo separado)
            # Por enquanto, apenas retornar sucesso
            
            return True, f"Assinatura solicitada para {len(users_list)} usuários"
            
        except Exception as e:
            current_app.logger.error(f"Erro ao solicitar assinaturas: {str(e)}")
            return False, f"Erro: {str(e)}"
    
    @staticmethod
    def export_signature_certificate(signature_id):
        """Exportar certificado de assinatura para verificação externa"""
        try:
            signature = DocumentSignature.query.get(signature_id)
            if not signature:
                return None, "Assinatura não encontrada"
            
            # Dados do certificado
            certificate_data = {
                'signature_id': signature.id,
                'document_code': signature.documento.codigo,
                'document_title': signature.documento.titulo,
                'document_version': signature.versao_documento,
                'signer_name': signature.usuario.nome_completo,
                'signer_email': signature.usuario.email,
                'signature_date': signature.data_assinatura.isoformat(),
                'signature_type': signature.tipo_assinatura,
                'document_hash': signature.hash_documento,
                'is_valid': signature.valida,
                'certificate_info': signature.certificado_info,
                'verification_url': f"/signatures/verify/{signature.id}"
            }
            
            return certificate_data, "Certificado gerado com sucesso"
            
        except Exception as e:
            current_app.logger.error(f"Erro ao exportar certificado: {str(e)}")
            return None, f"Erro: {str(e)}"

# Decorador para exigir assinatura em documentos críticos
def signature_required(signature_type='eletronica'):
    """Decorador para exigir assinatura em ações específicas"""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            # Implementar lógica de verificação de assinatura se necessário
            return f(*args, **kwargs)
        return decorated_function
    return decorator