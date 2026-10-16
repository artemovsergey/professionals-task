/* ===========================================================================
   ТОиР-Проф — эндпоинты API, собранные в одном месте.
   Страницы не строят строки запросов вручную: адреса меняются только здесь,
   и одна опечатка не размазывается по десяти экранам.
   =========================================================================== */

import { buildQuery, http } from './http'
import type {
  AnalyticsReport,
  AssignCrewDto,
  ChangeStatusDto,
  CompleteMaintenanceScheduleDto,
  CompleteWorkOrderDto,
  CreateReportDto,
  CreateWorkOrderDto,
  CrewDto,
  CrewShortDto,
  DashboardSummary,
  EquipmentDto,
  EquipmentShortDto,
  MaintenanceScheduleDto,
  MaintenanceTypeDto,
  MaterialDto,
  MaterialShortageDto,
  MaterialWriteOffDto,
  PagedResult,
  ReportLink,
  ScheduleStatus,
  WorkOrderDto,
  WorkOrderShortDto,
  WorkOrderStatus,
  WorkshopDto,
} from './types'

/* ------------------------------ Оборудование ---------------------------- */

export interface EquipmentQuery {
  workshopId?: string
  search?: string
  status?: string
  criticality?: number
  includeRetired?: boolean
  page?: number
  pageSize?: number
}

export const equipmentApi = {
  list: (q: EquipmentQuery, signal?: AbortSignal) =>
    http.get<PagedResult<EquipmentShortDto>>(`/equipment${buildQuery({ ...q })}`, signal),
  forSelect: (signal?: AbortSignal) => http.get<EquipmentShortDto[]>('/equipment/select', signal),
  byId: (id: string, signal?: AbortSignal) => http.get<EquipmentDto>(`/equipment/${id}`, signal),
  create: (body: unknown) => http.post<EquipmentDto>('/equipment', body),
  update: (id: string, body: unknown) => http.put<EquipmentDto>(`/equipment/${id}`, body),
  changeStatus: (id: string, status: string) => http.patch<EquipmentDto>(`/equipment/${id}/status`, { status }),
}

/* ------------------------------ Справочники ----------------------------- */

export const maintenanceTypesApi = {
  list: (includeInactive: boolean, signal?: AbortSignal) =>
    http.get<MaintenanceTypeDto[]>(`/maintenance-types${buildQuery({ includeInactive })}`, signal),
}

/* -------------------------------- Цеха ---------------------------------- */

export const workshopsApi = {
  // Отдельного эндпоинта цехов в API нет: справочник приезжает в составе
  // среза дашборда, а для фильтров достаточно списка из оборудования.
  fromEquipment: (rows: EquipmentShortDto[]): WorkshopDto[] => {
    const seen = new Map<string, WorkshopDto>()
    for (const row of rows) {
      if (!seen.has(row.workshopId)) {
        seen.set(row.workshopId, { id: row.workshopId, code: '', name: row.workshopName })
      }
    }
    return [...seen.values()]
  },
}

/* ------------------------------ График ТО ------------------------------- */

export interface ScheduleQuery {
  equipmentId?: string
  from?: string
  to?: string
  status?: ScheduleStatus
}

export const scheduleApi = {
  list: (q: ScheduleQuery, signal?: AbortSignal) =>
    http.get<MaintenanceScheduleDto[]>(`/maintenance-schedule${buildQuery({ ...q })}`, signal),
  complete: (id: string, body: CompleteMaintenanceScheduleDto) =>
    http.post<MaintenanceScheduleDto>(`/maintenance-schedule/${id}/complete`, body),
  returnToPlan: (id: string) => http.post<MaintenanceScheduleDto>(`/maintenance-schedule/${id}/plan`, {}),
}

/* -------------------------------- Заявки -------------------------------- */

export interface WorkOrderQuery {
  equipmentId?: string
  crewId?: string
  status?: WorkOrderStatus
  priority?: string
  from?: string
  to?: string
  query?: string
  sort?: string
  order?: string
  page?: number
  pageSize?: number
}

export const workOrdersApi = {
  list: (q: WorkOrderQuery, signal?: AbortSignal) =>
    http.get<PagedResult<WorkOrderShortDto>>(`/work-orders${buildQuery({ ...q })}`, signal),
  recent: (limit: number, signal?: AbortSignal) =>
    http.get<PagedResult<WorkOrderShortDto>>(
      `/work-orders${buildQuery({ pageSize: limit, sort: 'createdAt', order: 'desc' })}`,
      signal,
    ),
  byId: (id: string, signal?: AbortSignal) => http.get<WorkOrderDto>(`/work-orders/${id}`, signal),
  byNumber: (number: string, signal?: AbortSignal) => http.get<WorkOrderDto>(`/work-orders/by-number/${number}`, signal),
  create: (body: CreateWorkOrderDto, userId: string) =>
    http.post<WorkOrderDto>(`/work-orders${buildQuery({ userId })}`, body),
  assignCrew: (id: string, body: AssignCrewDto) => http.post<WorkOrderDto>(`/work-orders/${id}/crew`, body),
  start: (id: string, actualStart: string) => http.post<WorkOrderDto>(`/work-orders/${id}/start`, { actualStart }),
  complete: (id: string, body: CompleteWorkOrderDto) => http.post<WorkOrderDto>(`/work-orders/${id}/complete`, body),
  changeStatus: (id: string, body: ChangeStatusDto) => http.post<WorkOrderDto>(`/work-orders/${id}/status`, body),
  writeOff: (id: string, body: MaterialWriteOffDto) => http.post<WorkOrderDto>(`/work-orders/${id}/materials`, body),
}

/* -------------------------------- Бригады -------------------------------- */

export const crewsApi = {
  list: (q: { includeInactive?: boolean; search?: string; page?: number; pageSize?: number }, signal?: AbortSignal) =>
    http.get<PagedResult<CrewDto>>(`/crews${buildQuery({ ...q })}`, signal),
  forSelect: (signal?: AbortSignal) => http.get<CrewShortDto[]>('/crews/select', signal),
  byId: (id: string, signal?: AbortSignal) => http.get<CrewDto>(`/crews/${id}`, signal),
}

/* ------------------------------- Материалы ------------------------------ */

export const materialsApi = {
  list: (
    q: { includeInactive?: boolean; search?: string; onlyShortage?: boolean; page?: number; pageSize?: number },
    signal?: AbortSignal,
  ) => http.get<PagedResult<MaterialDto>>(`/materials${buildQuery({ ...q })}`, signal),
  forSelect: (signal?: AbortSignal) => http.get<MaterialDto[]>('/materials/select', signal),
  shortages: (signal?: AbortSignal) => http.get<MaterialShortageDto[]>('/materials/shortages', signal),
  receive: (id: string, quantity: number) =>
    http.post<MaterialDto>(`/materials/${id}/receipt`, { quantity }),
}

/* ------------------------------- Дашборд -------------------------------- */

export const dashboardApi = {
  summary: (from: string, to: string, signal?: AbortSignal) =>
    http.get<DashboardSummary>(`/dashboard/summary${buildQuery({ from, to })}`, signal),
  analytics: (from: string, to: string, workshopId: string | undefined, signal?: AbortSignal) =>
    http.get<AnalyticsReport>(`/analytics${buildQuery({ from, to, workshopId })}`, signal),
}

/* -------------------------------- Отчёты -------------------------------- */

export const reportsApi = {
  createLink: (body: CreateReportDto) => http.post<ReportLink>('/reports', body),
  /** Адрес временной ссылки. Ссылка живёт 15 секунд — это требование листа. */
  downloadUrl: (url: string) => url,
}

/** Путь потока событий дашборда. */
export const DASHBOARD_EVENTS_PATH = '/api/dashboard/events'
