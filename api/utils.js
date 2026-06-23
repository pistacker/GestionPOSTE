export function createErrorResponse(message, status = 400) {
  return { statusCode: status, body: JSON.stringify({ error: message }) };
}

export function createSuccessResponse(payload, status = 200) {
  return { statusCode: status, body: JSON.stringify(payload) };
}
