"""Permissões do HubFlow: as padrão do Django (add/change/delete/view por model) + 2 específicas.

Regras que não cabem numa permissão ficam no código: sem `boards.change_card`/`delete_card` a pessoa só
edita/exclui os próprios cards; sem `clients.view_client` só vê os clientes de que é membro (Membership).
"""

# Específicas (registradas no model Access): não têm equivalente padrão.
CUSTOM_PERMISSIONS = {
    'use_cli': 'Usar a CLI',
    'view_own_payments': 'Ver os pagamentos dos seus clientes',
}

# Rótulos em português para a tela de permissões (as padrão vêm do Django).
LABELS = {
    'clients.view_client': 'Ver todos os clientes',
    'clients.add_client': 'Criar clientes',
    'clients.change_client': 'Editar clientes',
    'clients.delete_client': 'Excluir clientes',
    'projects.add_project': 'Criar projetos',
    'projects.change_project': 'Editar projetos',
    'projects.delete_project': 'Excluir projetos',
    'boards.add_card': 'Criar cards',
    'boards.change_card': 'Editar e mover qualquer card',
    'boards.delete_card': 'Excluir qualquer card',
    'boards.delete_comment': 'Excluir comentários de outros',
    'boards.add_label': 'Criar etiquetas',
    'boards.change_label': 'Editar etiquetas',
    'boards.delete_label': 'Excluir etiquetas',
    'sprints.add_sprint': 'Criar sprints',
    'sprints.change_sprint': 'Editar e fechar sprints',
    'sprints.delete_sprint': 'Excluir sprints',
    'sprints.add_milestone': 'Criar milestones',
    'sprints.change_milestone': 'Editar milestones',
    'billing.view_payment': 'Ver todos os pagamentos',
    'billing.add_payment': 'Criar pagamentos',
    'billing.change_payment': 'Editar, pagar e copiar pagamentos',
    'billing.delete_payment': 'Excluir pagamentos',
    'accounts.view_user': 'Ver usuários',
    'accounts.add_user': 'Convidar usuários',
    'accounts.change_user': 'Gerenciar papéis e permissões',
    'permissions.use_cli': 'Usar a CLI',
    'permissions.view_own_payments': 'Ver os pagamentos dos seus clientes',
}

ALL = list(LABELS)

CLIENTS_AND_PROJECTS = [p for p in ALL if p.startswith(('clients.', 'projects.'))]
CARDS = ['boards.add_card', 'boards.change_card', 'boards.delete_card', 'boards.delete_comment']
LABELS_PERMS = ['boards.add_label', 'boards.change_label', 'boards.delete_label']
SPRINTS = [p for p in ALL if p.startswith('sprints.')]
PAYMENTS_ALL = ['billing.view_payment', 'billing.add_payment', 'billing.change_payment', 'billing.delete_payment']

ROLES = {
    'Administrador': ALL,
    'Gerente': CLIENTS_AND_PROJECTS + CARDS + LABELS_PERMS + SPRINTS + ['billing.view_payment', 'permissions.use_cli'],
    'Desenvolvedor': ['boards.add_card'] + LABELS_PERMS + ['permissions.use_cli'],
    'Financeiro': ['clients.view_client'] + PAYMENTS_ALL,
    'Cliente': ['permissions.view_own_payments'],
    'Leitura': [],
}
