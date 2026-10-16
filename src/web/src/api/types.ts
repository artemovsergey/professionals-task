/* ===========================================================================
   ТОиР-Проф — контракты API для веб-клиента.
   Файлы повторяют DTO проекта api (src/api/DTOs) один в один. Схема БД и
   контракты API меняются только согласованно, поэтому и здесь типы описаны
   явно, а не через `any`: опечатка в названии поля должна ловиться сборкой.
   =========================================================================== */

/* ------------------------------- Общие ---------------------------------- */

export type EquipmentStatus = 'Работает' | 'В ремонте' | 'Выведено из эксплуатации'
export type WorkOrderStatus = 'Черновик' | 'Назначена' | 'В работе' | 'Завершена' | 'Отменена'
export type WorkOrderPriority = 'Низкий' | 'Средний' | 'Высокий' | 'Аварийный'
export type ScheduleStatus = 'Запланировано' | 'Выполнено' | 'Просрочено'
export type RoleCode = 'ADMIN' | 'MANAGER' | 'MASTER'

export interface PagedResult<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

export interface UserDto {
  id: string
  username: string
  fullName: string
  role: string
  isActive: boolean
  crews: string | null
  createdAt: string
}

export interface TokenResponse {
  token: string
  tokenType: string
  expiresIn: number
  user: UserDto
}

/* ------------------------------ Оборудование ---------------------------- */

export interface EquipmentShortDto {
  id: string
  inventoryNumber: string
  name: string
  workshopId: string
  workshopName: string
  status: EquipmentStatus
  criticality: number
}

export interface EquipmentDto {
  id: string
  inventoryNumber: string
  name: string
  workshopId: string
  workshopName: string
  manufacturer: string | null
  model: string | null
  serialNumber: string | null
  commissionDate: string
  decommissionDate: string | null
  status: EquipmentStatus
  criticality: number
  location: string | null
  notes: string | null
  createdAt: string
  updatedAt: string
  isDecommissioned: boolean
}

export interface WorkshopDto {
  id: string
  code: string
  name: string
}

/* -------------------------- Справочник видов ТО ------------------------- */

export interface MaintenanceTypeDto {
  id: string
  code: string
  name: string
  intervalDays: number
  description: string | null
  isActive: boolean
  usageCount: number
}

/* ------------------------------ График ТО ------------------------------- */

export interface MaintenanceScheduleDto {
  id: string
  equipmentId: string
  equipmentName: string
  inventoryNumber: string
  maintenanceTypeId: string
  maintenanceTypeName: string
  intervalDays: number
  plannedDate: string
  completedDate: string | null
  nextPlannedDate: string | null
  status: ScheduleStatus
  actualCost: number | null
  notes: string | null
}

/* -------------------------------- Заявки --------------------------------- */

export interface WorkOrderShortDto {
  id: string
  number: string
  equipmentId: string
  equipmentName: string
  inventoryNumber: string
  priority: WorkOrderPriority
  status: WorkOrderStatus
  plannedStart: string | null
  plannedEnd: string | null
  downtimeHours: number | null
  crewName: string | null
}

export interface WorkOrderMaterialDto {
  materialId: string
  sku: string
  name: string
  unit: string
  quantity: number
  unitPrice: number
  cost: number
}

export interface WorkOrderHistoryDto {
  changedAt: string
  changedByName: string | null
  action: string
  summary: string
}

export interface WorkOrderDto {
  id: string
  number: string
  equipmentId: string
  equipmentName: string
  inventoryNumber: string
  workshopName: string
  maintenanceTypeId: string | null
  maintenanceTypeName: string | null
  crewId: string | null
  crewName: string | null
  assignedTo: string | null
  assignedToName: string | null
  title: string
  description: string
  priority: WorkOrderPriority
  status: WorkOrderStatus
  plannedStart: string | null
  plannedEnd: string | null
  actualStart: string | null
  actualEnd: string | null
  downtimeHours: number | null
  failureReason: string | null
  completedAt: string | null
  createdOn: string
  totalMaterialCost: number
  materials: WorkOrderMaterialDto[]
  history: WorkOrderHistoryDto[]
  hasDowntime: boolean
}

export interface MaterialCostDto {
  workOrderId: string
  totalCost: number
  positions: number
}

/* -------------------------------- Бригады -------------------------------- */

export interface CrewMemberDto {
  userId: string
  username: string
  fullName: string
  joinedAt: string
}

export interface CrewShortDto {
  id: string
  code: string
  name: string
  isActive: boolean
  memberCount: number
}

export interface CrewDto {
  id: string
  code: string
  name: string
  specialty: string | null
  isActive: boolean
  members: CrewMemberDto[]
  activeOrders: number
  completedOrders: number
  totalDowntimeHours: number
  rating: number
  efficiencyPercent: number
}

/* ------------------------------- Материалы ------------------------------- */

export interface MaterialDto {
  id: string
  sku: string
  name: string
  unit: string
  price: number
  stock: number
  minStock: number
  location: string | null
  isActive: boolean
  totalWrittenOff: number | null
  isShortage: boolean
}

export interface MaterialShortageDto {
  id: string
  sku: string
  name: string
  stock: number
  minStock: number
  unit: string
}

/* -------------------------------- Дашборд ------------------------------- */

export interface WorkshopSlice {
  workshopId: string
  name: string
  total: number
  completed: number
  downtimeHours: number
  averageDowntimeHours: number
}

export interface StatusSlice {
  status: string
  count: number
}

export interface MonthSlice {
  year: number
  month: number
  label: string
  count: number
  downtimeHours: number
}

export interface DashboardSummary {
  totalOrders: number
  inProgress: number
  completed: number
  averageDowntimeHours: number
  emergencyShare: number
  maintenancePlanShare: number
  totalMaterialCost: number
  byWorkshop: WorkshopSlice[]
  byStatus: StatusSlice[]
  byMonth: MonthSlice[]
  periodFrom: string
  periodTo: string
}

/* ------------------------------- Аналитика ------------------------------ */

export interface DowntimeSlice {
  equipmentId: string
  inventoryNumber: string
  name: string
  workshopName: string
  ordersCount: number
  totalDowntimeHours: number
  sharePercent: number
}

export interface CrewEfficiency {
  crewId: string
  code: string
  name: string
  assigned: number
  completed: number
  inTime: number
  averageDowntimeHours: number
  totalMaterialCost: number
  rating: number
}

export interface MaterialUsage {
  materialId: string
  sku: string
  name: string
  unit: string
  quantity: number
  cost: number
  ordersCount: number
}

export interface PlanExecutionSlice {
  status: ScheduleStatus
  count: number
  percent: number
}

export interface OrdersSummary {
  total: number
  completed: number
  inProgress: number
  cancelled: number
  completionShare: number
  emergencyShare: number
  averageDowntimeHours: number
}

export interface AnalyticsReport {
  periodFrom: string
  periodTo: string
  downtime: DowntimeSlice[]
  crews: CrewEfficiency[]
  materials: MaterialUsage[]
  plan: PlanExecutionSlice[]
  orders: OrdersSummary
}

/* -------------------------------- Отчёты -------------------------------- */

export type ReportKind = 'downtime' | 'crews' | 'materials' | 'plan'

export interface CreateReportDto {
  kind: ReportKind
  from?: string
  to?: string
  workshopId?: string
}

export interface ReportLink {
  token: string
  url: string
  expiresAt: string
  ttlSeconds: number
  ttlSecondsValue: number
}

export interface DashboardEvent {
  type: string
  at: string
  data: DashboardSummary
}

/* ------------------------------ Справочники ----------------------------- */

export const EQUIPMENT_STATUSES: readonly EquipmentStatus[] = [
  'Работает',
  'В ремонте',
  'Выведено из эксплуатации',
]

export const WORK_ORDER_STATUSES: readonly WorkOrderStatus[] = [
  'Черновик',
  'Назначена',
  'В работе',
  'Завершена',
  'Отменена',
]

export const WORK_ORDER_PRIORITIES: readonly WorkOrderPriority[] = [
  'Низкий',
  'Средний',
  'Высокий',
  'Аварийный',
]

export const SCHEDULE_STATUSES: readonly ScheduleStatus[] = [
  'Запланировано',
  'Выполнено',
  'Просрочено',
]

export const REPORT_KINDS: readonly { kind: ReportKind; title: string }[] = [
  { kind: 'downtime', title: 'Простои' },
  { kind: 'crews', title: 'Бригады' },
  { kind: 'materials', title: 'Материалы' },
  { kind: 'plan', title: 'План ТО' },
]

/* ------------------------- Тело запросов (POST/PUT) ----------------------- */

export interface LoginDto {
  username: string
  password: string
}

export interface CreateEquipmentDto {
  inventoryNumber: string
  name: string
  workshopId: string
  manufacturer?: string | null
  model?: string | null
  serialNumber?: string | null
  commissionDate: string
  decommissionDate?: string | null
  status?: EquipmentStatus
  criticality?: number
  location?: string | null
  notes?: string | null
}

export interface CreateWorkOrderDto {
  equipmentId: string
  maintenanceTypeId?: string | null
  scheduleId?: string | null
  title: string
  description: string
  priority?: WorkOrderPriority
  plannedStart?: string | null
  plannedEnd?: string | null
  crewId?: string | null
}

export interface AssignCrewDto {
  crewId: string
  assignedTo?: string | null
}

export interface StartWorkOrderDto {
  actualStart: string
}

export interface CompleteWorkOrderDto {
  actualEnd: string
  failureReason: string
  comment?: string | null
}

export interface ChangeStatusDto {
  status: WorkOrderStatus
  reason?: string | null
}

export interface MaterialWriteOffDto {
  materialId: string
  quantity: number
}

export interface CompleteMaintenanceScheduleDto {
  completedDate: string
  actualCost?: number | null
}
