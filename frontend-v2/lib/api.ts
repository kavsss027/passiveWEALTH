import { ReconstructionRequest, ReconstructionResponse } from './types'

const BASE_URL = 'http://127.0.0.1:8000/api/v1'

export async function reconstructPortfolio(
  request: ReconstructionRequest
): Promise<ReconstructionResponse> {
  const response = await fetch(`${BASE_URL}/portfolio/reconstruct`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error?.error?.message ?? 'Reconstruction failed')
  }

  return response.json()
}
