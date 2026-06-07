// Central mock data — will be replaced by API calls

export const SKILLS = [
  { id: 1, name: 'React / Frontend', color: 'bg-blue-100 text-blue-700' },
  { id: 2, name: 'Node.js / Backend', color: 'bg-green-100 text-green-700' },
  { id: 3, name: 'Python', color: 'bg-yellow-100 text-yellow-700' },
  { id: 4, name: 'UI/UX Design', color: 'bg-pink-100 text-pink-700' },
  { id: 5, name: 'DevOps / CI-CD', color: 'bg-orange-100 text-orange-700' },
  { id: 6, name: 'Data / SQL', color: 'bg-purple-100 text-purple-700' },
  { id: 7, name: 'Mobile (React Native)', color: 'bg-indigo-100 text-indigo-700' },
  { id: 8, name: 'QA / Tests', color: 'bg-red-100 text-red-700' },
]

export interface MockEmployee {
  id: number
  name: string
  role: string
  skillIds: number[]
  // Absences: array of { start, end } ISO strings
  absences: { start: string; end: string }[]
  // Active project IDs
  activeProjectIds: number[]
  // Occupation % this month (0-100)
  occupation: number
}

export const EMPLOYEES: MockEmployee[] = [
  {
    id: 1, name: 'Sophie Martin', role: 'employee',
    skillIds: [1, 4, 7],
    absences: [],
    activeProjectIds: [1],
    occupation: 80,
  },
  {
    id: 2, name: 'Lucas Bernard', role: 'manager',
    skillIds: [2, 5, 6],
    absences: [],
    activeProjectIds: [1, 2],
    occupation: 100,
  },
  {
    id: 3, name: 'Emma Dubois', role: 'employee',
    skillIds: [1, 2, 8],
    absences: [{ start: '2026-05-05', end: '2026-05-09' }],
    activeProjectIds: [3],
    occupation: 60,
  },
  {
    id: 4, name: 'Thomas Petit', role: 'admin',
    skillIds: [3, 6, 5],
    absences: [],
    activeProjectIds: [],
    occupation: 20,
  },
  {
    id: 5, name: 'Camille Leroy', role: 'employee',
    skillIds: [4, 1],
    absences: [{ start: '2026-05-12', end: '2026-05-23' }],
    activeProjectIds: [2],
    occupation: 90,
  },
  {
    id: 6, name: 'Antoine Moreau', role: 'employee',
    skillIds: [2, 3, 6],
    absences: [],
    activeProjectIds: [],
    occupation: 30,
  },
  {
    id: 7, name: 'Julie Fontaine', role: 'employee',
    skillIds: [7, 1, 8],
    absences: [],
    activeProjectIds: [1],
    occupation: 70,
  },
  {
    id: 8, name: 'Marc Dupont', role: 'employee',
    skillIds: [5, 2, 3],
    absences: [],
    activeProjectIds: [],
    occupation: 10,
  },
]

export interface SuggestedEmployee {
  employee: MockEmployee
  matchingSkills: number[]   // skill IDs that match
  matchCount: number
  available: boolean
  unavailableReason?: string
  occupation: number
}

/**
 * Suggest employees for a project given required skills and date range.
 * Filters out:
 *  - employees with no matching skills
 *  - employees absent for the entire period
 *  - employees at 100% occupation on other projects
 * Sorts by: matchCount desc, then occupation asc
 */
export function suggestEmployees(
  requiredSkillIds: number[],
  startDate: string,
  endDate: string,
): SuggestedEmployee[] {
  if (requiredSkillIds.length === 0) return []

  const start = new Date(startDate)
  const end = new Date(endDate)

  return EMPLOYEES
    .map(emp => {
      const matchingSkills = emp.skillIds.filter(s => requiredSkillIds.includes(s))
      if (matchingSkills.length === 0) return null

      // Check absence overlap
      const fullyAbsent = emp.absences.some(abs => {
        const absStart = new Date(abs.start)
        const absEnd = new Date(abs.end)
        return absStart <= start && absEnd >= end
      })

      const partiallyAbsent = emp.absences.some(abs => {
        const absStart = new Date(abs.start)
        const absEnd = new Date(abs.end)
        return absStart <= end && absEnd >= start
      })

      // Check if fully occupied
      const fullyOccupied = emp.occupation >= 100

      let available = true
      let unavailableReason: string | undefined

      if (fullyAbsent) {
        available = false
        unavailableReason = 'Absent sur toute la période'
      } else if (fullyOccupied) {
        available = false
        unavailableReason = 'Occupation 100% sur d\'autres projets'
      } else if (partiallyAbsent) {
        unavailableReason = 'Partiellement absent sur la période'
      }

      return {
        employee: emp,
        matchingSkills,
        matchCount: matchingSkills.length,
        available,
        unavailableReason,
        occupation: emp.occupation,
      } as SuggestedEmployee
    })
    .filter((s): s is SuggestedEmployee => s !== null)
    .sort((a, b) => {
      // Available first
      if (a.available !== b.available) return a.available ? -1 : 1
      // Then by match count desc
      if (b.matchCount !== a.matchCount) return b.matchCount - a.matchCount
      // Then by occupation asc
      return a.occupation - b.occupation
    })
}
