<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const users = ref([])
const catalog = ref({ roles: [], permissions: [] })
const clients = ref([])
const changes = ref([])
const selectedId = ref(null)
const error = ref('')
const notice = ref('')
const inviting = ref(false)
const invite = reactive({ email: '', name: '', role: 'Desenvolvedor', client_ids: [] })

const call = (path, options = {}) => api(path, { token: auth.token, ...options })
const selected = computed(() => users.value.find((u) => u.id === selectedId.value) || null)
const rolePerms = computed(() => {
  const perms = new Set()
  for (const role of catalog.value.roles) if (selected.value?.roles.includes(role.name)) role.permissions.forEach((p) => perms.add(p))
  return perms
})
const fromRole = (perm) => selected.value?.is_superuser || rolePerms.value.has(perm)
const hasPerm = (perm) => selected.value?.permissions.includes(perm)
const paymentsAccess = computed(() => {
  if (hasPerm('billing.view_payment')) return 'all'
  return hasPerm('permissions.view_own_payments') ? 'own' : 'none'
})

async function load() {
  ;[users.value, catalog.value, clients.value] = await Promise.all([call('/users/manage'), call('/users/catalog'), call('/clients')])
}

async function select(user) {
  selectedId.value = user.id
  error.value = notice.value = ''
  changes.value = await call(`/users/changes?user=${user.id}`)
}

// Toda alteração devolve a pessoa atualizada; troca na lista e recarrega o histórico.
async function update(path, body) {
  error.value = notice.value = ''
  try {
    const fresh = await call(`/users/${selected.value.id}/${path}`, { method: 'PUT', body })
    users.value = users.value.map((u) => (u.id === fresh.id ? fresh : u))
    changes.value = await call(`/users/changes?user=${fresh.id}`)
  } catch (e) {
    error.value = e.message
  }
}

const toggle = (list, item) => (list.includes(item) ? list.filter((x) => x !== item) : [...list, item])
const setRoles = (role) => update('roles', { roles: toggle(selected.value.roles, role) })
const setClients = (id) => update('clients', { client_ids: toggle(selected.value.clients.map((c) => c.id), id) })
const setExtra = (perms) => update('permissions', { permissions: perms })
const togglePerm = (perm) => setExtra(toggle(selected.value.extra_permissions, perm))

function setPayments(level) {
  const extra = selected.value.extra_permissions.filter((p) => !['billing.view_payment', 'permissions.view_own_payments'].includes(p))
  if (level === 'all') extra.push('billing.view_payment')
  if (level === 'own') extra.push('permissions.view_own_payments')
  setExtra(extra)
}

async function sendInvite() {
  error.value = notice.value = ''
  try {
    const user = await call('/users/invite', { method: 'POST', body: { email: invite.email, name: invite.name, roles: [invite.role], client_ids: invite.client_ids } })
    users.value = [...users.value, user].sort((a, b) => a.email.localeCompare(b.email))
    notice.value = `Convite enviado para ${user.email}.`
    Object.assign(invite, { email: '', name: '', client_ids: [] })
    inviting.value = false
  } catch (e) {
    error.value = e.message
  }
}

const when = (iso) => new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
const permLabel = computed(() => Object.fromEntries(catalog.value.permissions.map((p) => [p.code, p.label])))
const show = (values) =>
  values.length ? values.map((v) => (v === true ? 'ativo' : v === false ? 'inativo' : permLabel.value[v] || v)).join(', ') : '—'

onMounted(load)
</script>

<template>
  <div class="mx-auto flex max-w-[144rem] flex-col gap-4 lg:flex-row lg:items-start">
    <section class="min-w-0 flex-1">
      <div class="mb-4 flex items-center justify-between">
        <p class="text-muted">{{ users.length }} pessoa{{ users.length === 1 ? '' : 's' }}</p>
        <button v-if="auth.can('accounts.add_user')" type="button" class="btn btn-primary" @click="inviting = !inviting">Convidar pessoa</button>
      </div>

      <form v-if="inviting" class="panel mb-4 grid gap-3 p-4 sm:grid-cols-2" @submit.prevent="sendInvite">
        <div>
          <label class="label" for="invite-email">E-mail</label>
          <input id="invite-email" v-model="invite.email" class="field" type="email" placeholder="pessoa@hubflow.com" required />
        </div>
        <div>
          <label class="label" for="invite-name">Nome</label>
          <input id="invite-name" v-model="invite.name" class="field" type="text" />
        </div>
        <div>
          <label class="label" for="invite-role">Papel</label>
          <select id="invite-role" v-model="invite.role" class="field">
            <option v-for="role in catalog.roles" :key="role.name" :value="role.name">{{ role.name }}</option>
          </select>
        </div>
        <fieldset>
          <legend class="label">Clientes</legend>
          <label v-for="client in clients" :key="client.id" class="mr-3 inline-flex items-center gap-1.5 text-sm">
            <input v-model="invite.client_ids" type="checkbox" :value="client.id" class="h-4 w-4 accent-[var(--accent)]" /> {{ client.name }}
          </label>
        </fieldset>
        <p class="text-[0.93rem] text-muted sm:col-span-2">A pessoa recebe um e-mail com o link para definir a senha.</p>
        <div class="sm:col-span-2"><button type="submit" class="btn btn-primary">Enviar convite</button></div>
      </form>

      <p v-if="notice" class="mb-3 text-muted" role="status">{{ notice }}</p>
      <p v-if="error && !selected" class="mb-3 text-danger" role="alert">{{ error }}</p>

      <table v-stack class="stack-table panel w-full border-separate border-spacing-0 overflow-hidden">
        <thead>
          <tr class="text-left text-muted">
            <th class="border-b border-border px-4 py-2 font-medium">Pessoa</th>
            <th class="border-b border-border px-4 py-2 font-medium">Papéis</th>
            <th class="hidden border-b border-border px-4 py-2 font-medium md:table-cell">Clientes</th>
            <th class="border-b border-border px-4 py-2 font-medium">Situação</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="user in users"
            :key="user.id"
            class="cursor-pointer hover:bg-surface-2/60"
            :class="{ 'bg-surface-2': user.id === selectedId }"
            @click="select(user)"
          >
            <td class="border-b border-border px-4 py-2.5">
              <button type="button" class="text-left" @click.stop="select(user)">
                <span class="block font-medium">{{ user.name || user.email }}</span>
                <span class="block text-[0.93rem] text-muted">{{ user.email }}</span>
              </button>
            </td>
            <td class="border-b border-border px-4 py-2.5">{{ user.is_superuser ? 'Superusuário' : user.roles.join(', ') || '—' }}</td>
            <td class="hidden border-b border-border px-4 py-2.5 text-muted md:table-cell">{{ user.clients.map((c) => c.name).join(', ') || '—' }}</td>
            <td class="border-b border-border px-4 py-2.5" :class="user.is_active ? '' : 'text-muted'">{{ user.is_active ? 'ativo' : 'inativo' }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <aside v-if="selected" class="panel w-full shrink-0 divide-y divide-border lg:w-[26rem]" aria-label="Permissões da pessoa">
      <header class="flex items-center gap-2 p-4">
        <div class="min-w-0">
          <h2 class="truncate font-semibold">{{ selected.name || selected.email }}</h2>
          <p class="truncate text-[0.93rem] text-muted">{{ selected.email }}</p>
        </div>
        <button type="button" class="btn btn-ghost ml-auto h-8 w-8 justify-center px-0" aria-label="Fechar" @click="selectedId = null">×</button>
      </header>

      <p v-if="error" class="px-4 py-2 text-danger" role="alert">{{ error }}</p>
      <p v-if="selected.is_superuser" class="px-4 py-2 text-[0.93rem] text-muted">Superusuário: tem todas as permissões.</p>

      <fieldset class="p-4">
        <legend class="label px-0 pt-4">Papéis</legend>
        <label v-for="role in catalog.roles" :key="role.name" class="mr-3 inline-flex items-center gap-1.5 text-sm">
          <input type="checkbox" class="h-4 w-4 accent-[var(--accent)]" :checked="selected.roles.includes(role.name)" @change="setRoles(role.name)" />
          {{ role.name }}
        </label>
      </fieldset>

      <fieldset class="p-4">
        <legend class="label px-0 pt-4">Clientes vinculados</legend>
        <label v-for="client in clients" :key="client.id" class="mr-3 inline-flex items-center gap-1.5 text-sm">
          <input type="checkbox" class="h-4 w-4 accent-[var(--accent)]" :checked="selected.clients.some((c) => c.id === client.id)" @change="setClients(client.id)" />
          {{ client.name }}
        </label>
        <p class="mt-1 text-[0.93rem] text-muted">Sem "Ver todos os clientes", a pessoa só enxerga estes.</p>
      </fieldset>

      <div class="space-y-3 p-4">
        <label class="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            class="h-4 w-4 accent-[var(--accent)]"
            :checked="hasPerm('permissions.use_cli')"
            :disabled="fromRole('permissions.use_cli')"
            @change="togglePerm('permissions.use_cli')"
          />
          Usar a CLI <span v-if="fromRole('permissions.use_cli')" class="text-[0.93rem] text-muted">(vem do papel)</span>
        </label>
        <div>
          <p class="label">Pagamentos</p>
          <div class="flex flex-wrap gap-3 text-sm">
            <label v-for="[level, text] in [['all', 'todos'], ['own', 'só os seus'], ['none', 'nenhum']]" :key="level" class="inline-flex items-center gap-1.5">
              <input
                type="radio"
                name="payments"
                class="h-4 w-4 accent-[var(--accent)]"
                :checked="paymentsAccess === level"
                :disabled="fromRole('billing.view_payment') || (level !== 'all' && fromRole('permissions.view_own_payments'))"
                @change="setPayments(level)"
              />
              {{ text }}
            </label>
          </div>
        </div>
      </div>

      <details class="p-4">
        <summary class="cursor-pointer text-sm font-medium">Permissões por pessoa</summary>
        <p class="mt-2 text-[0.93rem] text-muted">As marcadas e travadas vêm do papel; as outras valem só para esta pessoa.</p>
        <ul class="mt-2 space-y-1">
          <li v-for="perm in catalog.permissions" :key="perm.code">
            <label class="flex items-center gap-2 text-sm" :title="perm.code">
              <input
                type="checkbox"
                class="h-4 w-4 accent-[var(--accent)]"
                :checked="hasPerm(perm.code)"
                :disabled="fromRole(perm.code)"
                @change="togglePerm(perm.code)"
              />
              {{ perm.label }}
            </label>
          </li>
        </ul>
      </details>

      <div class="flex items-center gap-2 p-4">
        <span class="text-sm">{{ selected.is_active ? 'Conta ativa' : 'Conta desativada' }}</span>
        <button
          v-if="selected.id !== auth.user?.id"
          type="button"
          class="btn ml-auto h-8"
          :class="{ 'text-danger': selected.is_active }"
          @click="update('active', { is_active: !selected.is_active })"
        >
          {{ selected.is_active ? 'Desativar' : 'Reativar' }}
        </button>
      </div>

      <section class="p-4">
        <h3 class="label">Histórico</h3>
        <ul class="space-y-2">
          <li v-for="change in changes" :key="change.id" class="text-sm">
            <p>
              <span class="font-medium">{{ change.action_label }}</span>: {{ show(change.before) }} → {{ show(change.after) }}
            </p>
            <p class="text-[0.93rem] text-muted">{{ change.changed_by || 'sistema' }} · {{ when(change.created) }}</p>
          </li>
          <li v-if="!changes.length" class="text-sm text-muted">Nenhuma alteração registrada.</li>
        </ul>
      </section>
    </aside>
  </div>
</template>
