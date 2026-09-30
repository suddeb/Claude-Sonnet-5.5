**Risk (SOQL in a loop):** Apex enforces a limit of 100 synchronous SOQL queries per transaction (200 async). A trigger receives up to 200 records per batch, so a query inside a `for` loop over `Trigger.new` runs once per record. Loading 101+ Cases (data loader, API, or a flow/process that fires more DML) throws `System.LimitException: Too many SOQL queries: 101`, rolling back the whole transaction. Since other triggers, flows, and managed packages share the same limit, even smaller batches can fail. It's also slow, wasting CPU time and database round-trips.

**Anti-pattern:**

```apex
trigger CaseTrigger on Case (before insert, before update) {
    for (Case c : Trigger.new) {
        Account a = [SELECT Id, Name, Industry FROM Account WHERE Id = :c.AccountId];
        if (a.Industry == 'Healthcare') {
            c.Priority = 'High';
        }
    }
}
```

**Bulkified rewrite:**

```apex
trigger CaseTrigger on Case (before insert, before update) {
    CaseTriggerHandler.setPriority(Trigger.new);
}
```

```apex
public with sharing class CaseTriggerHandler {
    public static void setPriority(List<Case> cases) {
        // 1. Collect IDs
        Set<Id> accountIds = new Set<Id>();
        for (Case c : cases) {
            if (c.AccountId != null) {
                accountIds.add(c.AccountId);
            }
        }
        if (accountIds.isEmpty()) return;

        // 2. One query, outside the loop
        Map<Id, Account> accounts = new Map<Id, Account>(
            [SELECT Id, Industry FROM Account WHERE Id IN :accountIds]
        );

        // 3. Loop and use the map
        for (Case c : cases) {
            Account a = accounts.get(c.AccountId);
            if (a != null && a.Industry == 'Healthcare') {
                c.Priority = 'High';
            }
        }
    }
}
```

**Key points:** collect IDs, query once with `IN :set`, store the results in a `Map`, then look records up by key in the loop. This uses 1 query whether there are 1 or 200 Cases. The same principle applies to DML: gather records in a list and perform one `insert`/`update` after the loop.