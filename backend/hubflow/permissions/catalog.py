"""Catálogo de permissões do HubFlow e papéis (grupos) padrão.

Combináveis por grupo e por pessoa; "seus" = clientes de que a pessoa é membro (Membership).
"""

PERMISSIONS = {
    'view_all_clients': 'Ver todos os clientes e projetos (sem isso, só os clientes de que é membro)',
    'manage_projects': 'Criar, editar e excluir clientes e projetos',
    'create_cards': 'Criar cards',
    'edit_any_card': 'Editar e mover qualquer card (sem isso, só os próprios)',
    'delete_any_card': 'Excluir qualquer card (sem isso, só os próprios)',
    'delete_any_comment': 'Excluir comentários de outras pessoas',
    'manage_sprints': 'Criar, editar e fechar sprints e milestones',
    'manage_labels': 'Criar, editar e excluir etiquetas',
    'view_all_payments': 'Ver todos os pagamentos',
    'view_own_payments': 'Ver os pagamentos dos seus clientes',
    'manage_payments': 'Criar, editar, pagar, copiar e excluir pagamentos',
    'use_cli': 'Usar a CLI',
    'manage_users': 'Gerenciar usuários, papéis e permissões',
}

ALL = list(PERMISSIONS)

ROLES = {
    'Administrador': ALL,
    'Gerente': [
        'view_all_clients',
        'manage_projects',
        'create_cards',
        'edit_any_card',
        'delete_any_card',
        'delete_any_comment',
        'manage_sprints',
        'manage_labels',
        'view_all_payments',
        'use_cli',
    ],
    'Desenvolvedor': ['create_cards', 'manage_labels', 'use_cli'],
    'Financeiro': ['view_all_clients', 'view_all_payments', 'manage_payments'],
    'Cliente': ['view_own_payments'],
    'Leitura': [],
}
