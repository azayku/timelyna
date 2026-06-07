import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getActiveTimer, startTimer, stopTimer } from './api'
import type { TimerStartPayload } from './api'
import Swal from 'sweetalert2'

export function useActiveTimer() {
  return useQuery({
    queryKey: ['active-timer'],
    queryFn: getActiveTimer,
    refetchInterval: 10000,
  })
}

export function useStartTimer() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: TimerStartPayload) => startTimer(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['active-timer'] })
      Swal.fire({
        icon: 'success',
        title: 'Timer démarré',
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3000,
      })
    },
    onError: () => {
      Swal.fire({
        icon: 'error',
        title: 'Erreur lors du démarrage du timer',
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3000,
      })
    },
  })
}

export function useStopTimer() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: stopTimer,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['active-timer'] })
      queryClient.invalidateQueries({ queryKey: ['timesheet-all-entries'] })
      queryClient.invalidateQueries({ queryKey: ['timesheet-week'] })
      Swal.fire({
        icon: 'success',
        title: `Timer arrêté — ${data.hours_worked.toFixed(2)}h enregistrées`,
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3000,
      })
    },
    onError: () => {
      Swal.fire({
        icon: 'error',
        title: 'Erreur lors de l\'arrêt du timer',
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3000,
      })
    },
  })
}
