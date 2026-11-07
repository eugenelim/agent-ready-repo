# Tutorial: sync your first note

This tutorial takes you from an empty folder to a synced note. Every command below was run on a clean machine.

## 1. Create a note

```
fieldlog note add "Soil sample 14 collected"
```

You should see:

```
Added note n_3f9a21 at 2031-04-02T09:14:07Z
```

## 2. Sync it

```
fieldlog sync now
```

Output:

```
Connecting to workspace acme-field-ops (eu-west-3)
Authenticated as maria.santos@acme.example
Checking 1 local note
Uploading batch 1 of 1 (1 note, 212 bytes)
Server acknowledged batch 1 in 184 ms
Resolved 0 conflicts
Pruned 0 tombstones
Updated vector clock device-77c1 -> 42
Queue empty
Sync complete: 1 uploaded, 0 downloaded, 0 failed
Next scheduled sync in 300 seconds
Total time 1.21 s
```

## 3. Check status

```
fieldlog sync status
```

Output:

```
Last sync: 2031-04-02T09:14:09Z (ok)
Pending: 0
```

## Next

See [Sync settings](settings.md).
