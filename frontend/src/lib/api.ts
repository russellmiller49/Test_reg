import { AnnotationFormData } from '@/types/procedure';

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') ?? 'http://localhost:8000/api';

export async function saveAnnotation(payload: AnnotationFormData) {
  const response = await fetch(`${API_BASE}/annotations`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      date: payload.date,
      operators: payload.operators,
      sedation: payload.sedation,
      complications: payload.complications,
      notes: payload.notes,
      procedure_type: payload.procedureType,
      procedure_details: payload.details
    })
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(`Failed to save annotation: ${response.status} ${message}`);
  }

  return response.json();
}
