export function reportLovableError(error: unknown, context?: Record<string, any>): void {
  console.error("[Application Error]", error, context);
}