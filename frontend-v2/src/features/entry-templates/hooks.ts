import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getMyTemplates,
  createTemplate,
  deleteTemplate,
  updateTemplate,
  type EntryTemplateCreate,
} from './api'

export function useMyTemplates() {
  return useQuery({
    queryKey: ['entry-templates'],
    queryFn: getMyTemplates,
  })
}

export function useCreateTemplate() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createTemplate,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['entry-templates'] }),
  })
}

export function useDeleteTemplate() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: deleteTemplate,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['entry-templates'] }),
  })
}

export function useUpdateTemplate() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<EntryTemplateCreate> }) =>
      updateTemplate(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['entry-templates'] }),
  })
}
