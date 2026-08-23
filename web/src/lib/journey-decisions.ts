/** Return the public fragment target only for semantic-ID journeys. */
export function decisionTargetId(
  decisionGateIds: readonly string[] | undefined,
  gateId: string,
): string | undefined {
  return decisionGateIds?.includes(gateId) ? `decision-${gateId}` : undefined;
}
