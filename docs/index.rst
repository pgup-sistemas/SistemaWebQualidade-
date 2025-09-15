
Documentação do Sistema Alpha Gestão Documental
==============================================

Bem-vindo à documentação oficial do Sistema Alpha Gestão Documental, uma solução completa para gestão de documentos, qualidade e conformidade.

.. toctree::
   :maxdepth: 2
   :caption: Conteúdo:

   introducao
   instalacao
   funcionalidades/index
   usuarios/index
   api/index
   desenvolvimento/index
   faq

Visão Geral do Sistema
====================

O Alpha Gestão Documental é um sistema web desenvolvido em Flask que oferece:

* **Gestão de Documentos**: Criação, edição, versionamento e controle de documentos
* **Sistema de Aprovação**: Fluxo de aprovação com múltiplos níveis
* **Gestão de Qualidade**: Controle de não conformidades e auditorias
* **Gestão de Equipamentos**: Controle de calibração e manutenção
* **Relatórios e Dashboard**: Análise de dados e KPIs
* **Sistema de Notificações**: Alertas automáticos para vencimentos

Principais Características
========================

.. mermaid::

   graph TD
       A[Sistema Alpha Gestão] --> B[Documentos]
       A --> C[Usuários e Grupos]
       A --> D[Qualidade]
       A --> E[Equipamentos]
       A --> F[Relatórios]
       
       B --> B1[Criação]
       B --> B2[Versionamento]
       B --> B3[Aprovação]
       B --> B4[Assinatura Digital]
       
       C --> C1[Perfis de Acesso]
       C --> C2[Grupos/Setores]
       C --> C3[Permissões]
       
       D --> D1[Não Conformidades]
       D --> D2[Auditorias]
       D --> D3[Planos de Ação]
       
       E --> E1[Calibração]
       E --> E2[Manutenção]
       E --> E3[Certificados]

Índices e Tabelas
================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
