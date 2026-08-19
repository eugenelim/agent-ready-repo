import { describe, expect, it } from 'vitest';
import { decisionTargetId } from '../lib/journey-decisions';

describe('journey decision fragments', () => {
  it('does not emit a decision fragment for display-only legacy decisions', () => {
    expect(decisionTargetId(undefined, 'G-classify')).toBeUndefined();
  });

  it('emits a semantic decision fragment only for an ordered decision ID', () => {
    expect(decisionTargetId(['approve-plan'], 'approve-plan')).toBe('decision-approve-plan');
    expect(decisionTargetId(['approve-plan'], 'merge-reviewed-change')).toBeUndefined();
  });

  it('keeps fragments stable when a gate label changes', () => {
    const decisionGateIds = ['approve-plan', 'merge-reviewed-change'];
    const gates = [
      { id: 'approve-plan', label: 'Approve the plan' },
      { id: 'merge-reviewed-change', label: 'Merge the reviewed change' },
    ];
    const changedCopy = gates.map((gate) => ({ ...gate, label: `${gate.label} now` }));

    expect(changedCopy.map((gate) => decisionTargetId(decisionGateIds, gate.id)))
      .toEqual(gates.map((gate) => decisionTargetId(decisionGateIds, gate.id)));
  });

  it('keeps fragments stable when decision display order changes', () => {
    const gateIds = ['approve-plan', 'merge-reviewed-change'];
    const originalOrder = ['approve-plan', 'merge-reviewed-change'];
    const reordered = [...originalOrder].reverse();

    expect(gateIds.map((id) => decisionTargetId(reordered, id)))
      .toEqual(gateIds.map((id) => decisionTargetId(originalOrder, id)));
  });
});
