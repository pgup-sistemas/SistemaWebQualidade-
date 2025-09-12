# Overview

Alpha Gestão Documental is a comprehensive document management system built with Flask. It provides document creation, version control, approval workflows, and user role-based access control. The system enables organizations to manage their document lifecycle from creation through approval, publishing, and archival, with features like document reading confirmations, expiration tracking, audit trails, non-conformity management (CAPA), internal audits, digital signatures, and advanced email notifications.

# User Preferences

Preferred communication style: Simple, everyday language.

# Recent Changes

**September 12, 2025**
- **Non-Conformity Management (CAPA)**: Complete module for managing non-conformities with corrective and preventive actions
- **Internal Audits Module**: Audit planning, execution with checklists, findings management, and compliance tracking
- **Digital Signature System**: Electronic and digital document signing with verification and certificate management
- **Advanced Email Notifications**: Automated notification system with templates for various events
- **Quality Management Menu**: New navigation section for quality-related modules
- **Enhanced Models**: Added NonConformity, CorrectiveAction, Audit, AuditChecklist, AuditFinding, DocumentSignature, EmailNotification

# System Architecture

## Backend Architecture
- **Framework**: Flask with modular blueprint structure for clean separation of concerns
- **Database**: SQLAlchemy ORM with SQLite as default (configurable via environment variables)
- **Authentication**: Flask-Login with session-based authentication and role-based access control
- **Security**: CSRF protection via Flask-WTF, password hashing with Werkzeug
- **Email**: Flask-Mail integration for notifications (SMTP configurable)

## Data Model Design
- **User Management**: Role-based system with 5 distinct user types (administrador, gestor_qualidade, aprovador_revisor, colaborador_leitor, auditor)
- **Document Lifecycle**: Version control system with DocumentVersion tracking, approval workflows, reading confirmations, and digital signatures
- **Quality Management**: Non-conformity tracking, CAPA actions, internal audit workflows, and compliance monitoring
- **Audit Trail**: Comprehensive tracking of document creation, modifications, approvals, user interactions, and quality activities

## Frontend Architecture
- **Template Engine**: Jinja2 with Bootstrap 5 for responsive UI
- **JavaScript**: Vanilla JS with Bootstrap components for interactive features
- **Rich Text Editing**: TinyMCE integration for document content creation
- **File Management**: Configurable upload system with 16MB file size limits

## Permission System
- **Hierarchical Roles**: Admin > Quality Manager > Approver/Reviewer > Reader > Auditor
- **Action-Based Permissions**: Granular control over document creation, approval, and administrative functions
- **Resource-Level Security**: Document-specific access controls and approval assignments

## Configuration Management
- **Environment-Based**: All sensitive configurations via environment variables
- **Deployment-Ready**: Separate development and production configurations
- **File Storage**: Configurable upload directories with automatic folder creation

# External Dependencies

## Core Framework Dependencies
- **Flask**: Web framework with SQLAlchemy, Login, Mail, and WTF extensions
- **Bootstrap 5**: Frontend CSS framework with responsive grid system
- **Bootstrap Icons**: Icon library for consistent UI elements
- **Cryptography**: Library for digital signature and encryption capabilities

## Rich Text Editor
- **TinyMCE**: Cloud-based rich text editor for document content creation
- **Integration**: Direct CDN integration for document editing capabilities

## Database Options
- **SQLite**: Default development database (file-based)
- **PostgreSQL**: Production-ready option via DATABASE_URL environment variable
- **SQLAlchemy**: ORM abstraction supporting multiple database backends

## Email Services
- **SMTP**: Configurable email server for system notifications
- **Environment Variables**: MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD for setup

## File Storage
- **Local File System**: Upload folder management with automatic directory creation
- **Configurable Limits**: 16MB maximum file size with extensible configuration

## Potential Integrations
- **Cloud Storage**: Ready for AWS S3, Google Cloud, or Azure Blob integration
- **Authentication**: Extensible for LDAP, SAML, or OAuth integration
- **Document Processing**: Framework ready for PDF generation and document conversion services