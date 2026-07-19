package terraform

import future.keywords.if

# --- Helpers ---

resource_changes := input.resource_changes

is_create_or_update(change) if {
	change.change.actions[_] == "create"
}

is_create_or_update(change) if {
	change.change.actions[_] == "update"
}

# --- Rule 1: No 0.0.0.0/0 ingress (aws_security_group inline rules) ---

deny[msg] if {
	change := resource_changes[_]
	change.type == "aws_security_group"
	is_create_or_update(change)
	rule := change.change.after.ingress[_]
	cidr := rule.cidr_blocks[_]
	cidr == "0.0.0.0/0"
	msg := sprintf(
		"aws_security_group %q has ingress from 0.0.0.0/0 — remove or restrict the CIDR",
		[change.address],
	)
}

deny[msg] if {
	change := resource_changes[_]
	change.type == "aws_security_group"
	is_create_or_update(change)
	rule := change.change.after.ingress[_]
	cidr := rule.ipv6_cidr_blocks[_]
	cidr == "::/0"
	msg := sprintf(
		"aws_security_group %q has ingress from ::/0 — remove or restrict the IPv6 CIDR",
		[change.address],
	)
}

# --- Rule 1b: No 0.0.0.0/0 ingress (aws_security_group_rule standalone resource) ---

deny[msg] if {
	change := resource_changes[_]
	change.type == "aws_security_group_rule"
	is_create_or_update(change)
	change.change.after.type == "ingress"
	cidr := change.change.after.cidr_blocks[_]
	cidr == "0.0.0.0/0"
	msg := sprintf(
		"aws_security_group_rule %q allows ingress from 0.0.0.0/0",
		[change.address],
	)
}

# --- Rule 1c: No 0.0.0.0/0 ingress (aws_vpc_security_group_ingress_rule) ---

deny[msg] if {
	change := resource_changes[_]
	change.type == "aws_vpc_security_group_ingress_rule"
	is_create_or_update(change)
	change.change.after.cidr_ipv4 == "0.0.0.0/0"
	msg := sprintf(
		"aws_vpc_security_group_ingress_rule %q allows ingress from 0.0.0.0/0",
		[change.address],
	)
}

# --- Rule 2: managed-by = "terraform" tag must be present ---
#
# Enforces the ADR-0004 tagging standard at the plan gate. Fires when a
# resource's `tags` map exists and managed-by is absent or wrong.
#
# Caveat: AWS resources using `provider.default_tags` have their tags
# applied at the provider level; the plan JSON may show an empty or absent
# `tags` map for such resources. This rule will not fire false positives in
# that case (is_object guard), but it also will not catch resources that
# rely solely on default_tags. Complement with an AWS Config rule for
# runtime enforcement.

deny[msg] if {
	change := resource_changes[_]
	startswith(change.type, "aws_")
	is_create_or_update(change)
	tags := change.change.after.tags
	is_object(tags)
	object.get(tags, "managed-by", "missing") != "terraform"
	msg := sprintf(
		"%q has tags block but managed-by != \"terraform\" (tagging standard ADR-0004)",
		[change.address],
	)
}
