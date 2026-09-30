## The Governor-Limit Risk

Salesforce allows **100 SOQL queries per synchronous transaction** (200 asynchronous). Triggers process records in chunks of **up to 200** when data arrives via Data Loader, the API, bulk DML, or Flows. A query inside a `for` loop runs once per record, so inserting 101+ Cases throws:

`System.LimitException: Too many SOQL queries: 101`

The entire transaction then rolls back. Smaller batches are also risky because the limit is **shared** across everything in the transaction: other triggers, Flows, workflow re-fires, and managed packages all draw from the same budget. Per-record queries also waste CPU time and count toward the 50,000-row query limit.

The fix is to **collect IDs first, run one query using `IN`, store the results in a `Map`, then loop again and look records up in memory.**

---

## Before (Not Bulk-Safe)

```apex
trigger CaseTrigger on Case (before insert, before update) {
    for (Case c : Trigger.new) {
        // One query per Case: fails at 101 records
        Account a = [SELECT Id, Rating FROM Account WHERE Id = :c.AccountId];
        if (a.Rating == 'Hot') {
            c.Priority = 'High';
        }
    }
}
```

## After (Bulkified)

```apex
trigger CaseTrigger on Case (before insert, before update) {

    // 1. Collect the parent IDs you need
    Set<Id> accountIds = new Set<Id>();
    for (Case c : Trigger.new) {
        if (c.AccountId != null) {
            accountIds.add(c.AccountId);
        }
    }

    // Skip the query entirely if there's nothing to look up
    if (accountIds.isEmpty()) {
        return;
    }

    // 2. One query for the whole batch, stored in a Map for O(1) lookups
    Map<Id, Account> accountsById = new Map<Id, Account>(
        [SELECT Id, Rating FROM Account WHERE Id IN :accountIds]
    );

    // 3. Loop again and use in-memory lookups (no SOQL here)
    for (Case c : Trigger.new) {
        Account a = accountsById.get(c.AccountId);
        if (a != null && a.Rating == 'Hot') {
            c.Priority = 'High';
        }
    }
}
```

### Why This Works
- **One SOQL query** runs whether the batch has 1 record or 200.
- A `Set` removes duplicate IDs, and a `Map` provides fast lookup by ID.
- The null checks handle Cases with no Account and Accounts that weren't returned (for example, because of sharing rules).
- Because this is a `before` trigger, modifying `Trigger.new` directly requires no extra DML.

**Best practice:** Move this logic into a handler class, such as `CaseTriggerHandler`. Then write a test class that inserts 200+ Cases to prove the trigger is bulk-safe.