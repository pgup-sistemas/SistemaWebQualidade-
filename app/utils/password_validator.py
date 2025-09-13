"""
Validador de senhas para Sistema Alpha Gestão Documental
"""
import re
from typing import List, Tuple

class PasswordValidator:
    """Classe para validar força e segurança de senhas"""
    
    # Lista de senhas comuns que devem ser rejeitadas
    COMMON_PASSWORDS = [
        '123456', 'password', '123456789', '12345678', '12345',
        '1234567', '1234567890', 'qwerty', 'abc123', '111111',
        '123123', 'admin', 'letmein', 'welcome', 'monkey',
        'password123', 'admin123', '123456a', 'qwerty123',
        '000000', '654321', '1q2w3e4r', 'qwertyuiop', '1qaz2wsx'
    ]
    
    @staticmethod
    def validate_password(password: str, username: str = '', email: str = '') -> Tuple[bool, List[str]]:
        """
        Valida uma senha com base em critérios de segurança
        
        Args:
            password: A senha a ser validada
            username: Nome de usuário (opcional)
            email: Email do usuário (opcional)
            
        Returns:
            Tuple(is_valid: bool, errors: List[str])
        """
        errors = []
        
        # Verificar tamanho mínimo
        if len(password) < 8:
            errors.append("A senha deve ter pelo menos 8 caracteres")
        
        # Verificar tamanho máximo
        if len(password) > 128:
            errors.append("A senha não pode ter mais de 128 caracteres")
        
        # Verificar se contém pelo menos uma letra minúscula
        if not re.search(r'[a-z]', password):
            errors.append("A senha deve conter pelo menos uma letra minúscula")
        
        # Verificar se contém pelo menos uma letra maiúscula
        if not re.search(r'[A-Z]', password):
            errors.append("A senha deve conter pelo menos uma letra maiúscula")
        
        # Verificar se contém pelo menos um número
        if not re.search(r'\d', password):
            errors.append("A senha deve conter pelo menos um número")
        
        # Verificar se contém pelo menos um caractere especial
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
            errors.append("A senha deve conter pelo menos um caractere especial (!@#$%^&*(),.?\":{}|<>)")
        
        # Verificar se não é uma senha comum
        if password.lower() in [p.lower() for p in PasswordValidator.COMMON_PASSWORDS]:
            errors.append("Esta senha é muito comum e insegura")
        
        # Verificar se não contém o nome de usuário
        if username and len(username) >= 3 and username.lower() in password.lower():
            errors.append("A senha não deve conter o nome de usuário")
        
        # Verificar se não contém parte do email
        if email:
            email_local = email.split('@')[0]
            if len(email_local) >= 3 and email_local.lower() in password.lower():
                errors.append("A senha não deve conter partes do seu email")
        
        # Verificar sequências simples
        if PasswordValidator._has_simple_sequences(password):
            errors.append("A senha não deve conter sequências simples (123, abc, etc.)")
        
        # Verificar repetições excessivas
        if PasswordValidator._has_excessive_repetition(password):
            errors.append("A senha não deve ter muitos caracteres repetidos")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _has_simple_sequences(password: str) -> bool:
        """Verifica se a senha contém sequências simples"""
        password = password.lower()
        
        # Sequências numéricas
        for i in range(len(password) - 2):
            if password[i:i+3].isdigit():
                nums = [int(c) for c in password[i:i+3]]
                if nums[1] == nums[0] + 1 and nums[2] == nums[1] + 1:
                    return True
                if nums[1] == nums[0] - 1 and nums[2] == nums[1] - 1:
                    return True
        
        # Sequências alfabéticas
        for i in range(len(password) - 2):
            if password[i:i+3].isalpha():
                chars = password[i:i+3]
                if (ord(chars[1]) == ord(chars[0]) + 1 and 
                    ord(chars[2]) == ord(chars[1]) + 1):
                    return True
                if (ord(chars[1]) == ord(chars[0]) - 1 and 
                    ord(chars[2]) == ord(chars[1]) - 1):
                    return True
        
        # Sequências de teclado
        keyboard_sequences = ['qwerty', 'asdf', 'zxcv', '123456', '098765']
        for seq in keyboard_sequences:
            if seq in password or seq[::-1] in password:
                return True
        
        return False
    
    @staticmethod
    def _has_excessive_repetition(password: str) -> bool:
        """Verifica se há repetição excessiva de caracteres"""
        for i in range(len(password) - 2):
            if password[i] == password[i+1] == password[i+2]:
                return True
        return False
    
    @staticmethod
    def calculate_strength(password: str) -> Tuple[int, str]:
        """
        Calcula a força da senha em uma escala de 0-100
        
        Returns:
            Tuple(score: int, description: str)
        """
        score = 0
        
        # Pontuação base por tamanho
        length = len(password)
        if length >= 8:
            score += 25
        if length >= 12:
            score += 10
        if length >= 16:
            score += 5
        
        # Pontuação por variedade de caracteres
        if re.search(r'[a-z]', password):
            score += 5
        if re.search(r'[A-Z]', password):
            score += 5
        if re.search(r'\d', password):
            score += 5
        if re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
            score += 10
        
        # Pontuação por diversidade de caracteres únicos
        unique_chars = len(set(password))
        if unique_chars >= 5:
            score += 5
        if unique_chars >= 10:
            score += 10
        
        # Penalidades
        if password.lower() in [p.lower() for p in PasswordValidator.COMMON_PASSWORDS]:
            score -= 25
        
        if PasswordValidator._has_simple_sequences(password):
            score -= 15
        
        if PasswordValidator._has_excessive_repetition(password):
            score -= 10
        
        # Garantir que o score esteja entre 0 e 100
        score = max(0, min(100, score))
        
        # Descrição da força
        if score < 30:
            description = "Muito fraca"
        elif score < 50:
            description = "Fraca"
        elif score < 70:
            description = "Moderada"
        elif score < 85:
            description = "Forte"
        else:
            description = "Muito forte"
        
        return score, description
    
    @staticmethod
    def generate_suggestions(password: str) -> List[str]:
        """Gera sugestões para melhorar a senha"""
        suggestions = []
        
        if len(password) < 8:
            suggestions.append("Adicione mais caracteres (mínimo 8)")
        
        if not re.search(r'[a-z]', password):
            suggestions.append("Adicione letras minúsculas")
        
        if not re.search(r'[A-Z]', password):
            suggestions.append("Adicione letras maiúsculas")
        
        if not re.search(r'\d', password):
            suggestions.append("Adicione números")
        
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
            suggestions.append("Adicione símbolos especiais")
        
        if PasswordValidator._has_simple_sequences(password):
            suggestions.append("Evite sequências simples como 123 ou abc")
        
        if PasswordValidator._has_excessive_repetition(password):
            suggestions.append("Evite muitos caracteres repetidos")
        
        return suggestions