import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'

export type CurrencyOption = {
  code: string
  name: string
  symbol: string
}

type CurrencyResponse = CurrencyOption & {
  currencies: CurrencyOption[]
}

export function useCurrency() {
  const { data } = useQuery<CurrencyResponse>({
    queryKey: ['currency-setting'],
    queryFn: () => api.get('/core/settings/currency/').then(r => r.data),
    staleTime: 5 * 60 * 1000,
  })

  return {
    symbol: data?.symbol ?? 'BND$',
    code: data?.code ?? 'BND',
    name: data?.name ?? 'Brunei Dollar',
    currencies: data?.currencies ?? [],
  }
}
