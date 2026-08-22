# Orders architecture foundation

- Routes parse HTTP and call application use cases.
- Tenant context is required for every order-store operation.
- Recovery workers use a scoped service principal and preserve the job tenant.
