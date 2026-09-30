## The Risk

Salesforce allows **100 SOQL queries per synchronous transaction**. Triggers process records in chunks of up to **200** (e.g., Data Loader, API calls, mass updates), so a query inside a loop runs once per record. At the 101st query, Salesforce throws `System.LimitException: Too many SOQL queries: 101`, and the **entire batch rolls back**, not just the failing record.

The limit is also **shared across the whole transaction**. Other triggers, flows, and managed packages draw from the same 100-query budget, so failures can occur with far fewer records. Per-record querying also wastes CPU time and can approach the 50,000-row retrieval limit.

**Fix:** Collect the needed IDs into a `Set`, run **one** query outside the loop, store the results in a `Map`, and look records up in memory.

---

## Anti-Pattern (Before)

```apex
trigger CaseTrigger on Case (before insert, before update) {
    for (Case c : Trigger.new) {
        // One query PER case. Fails beyond 100 records.
        Account acc = [SELECT Id, Rating FROM Account WHERE Id = :c.AccountId];
        if (acc.Rating == 'Hot') {
            c.Priority = 'High';
        }
    }
}
```

## Bulkified Rewrite (After)

```apex
trigger CaseTrigger on Case (before insert, before update) {

    // 1. Collect the keys
    Set<Id> accountIds = new Set<Id>();
    for (Case c : Trigger.new) {
        if (c.AccountId != null) {
            accountIds.add(c.AccountId);
        }
    }

    if (accountIds.isEmpty()) {
        return;
    }

    // 2. Run a single query, stored in a Map for O(1) lookups
    Map<Id, Account> accountsById = new Map<Id, Account>(
        [SELECT Id, Rating FROM Account WHERE Id IN :accountIds]
    );

    // 3. Process records in memory, with no further SOQL
    for (Case c : Trigger.new) {
        Account acc = accountsById.get(c.AccountId);
        if (acc != null && acc.Rating == 'Hot') {
            c.Priority = 'High';
        }
    }
}
```

**Result:** This uses 1 query whether the batch has 1 record or 200.

**Additional best practices:**
- Move the logic into a trigger handler class, following the one-trigger-per-object pattern.
- On update, only process cases whose `AccountId` actually changed (compare against `Trigger.oldMap`).
- Write a test that inserts 200+ cases to prove the trigger is bulk-safe.