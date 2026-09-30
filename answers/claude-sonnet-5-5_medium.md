**Risk:** Salesforce limits a single transaction to 100 synchronous SOQL queries (200 async). A trigger can receive up to 200 records per batch, so a query inside a `for` loop runs once per record. Loading 101+ Cases (data loader, API, or a flow that updates many) throws `System.LimitException: Too many SOQL queries: 101`, and the whole transaction rolls back. The same applies to DML in loops (150 statement limit). It may pass in testing with a single record and then fail in production with bulk loads. Other triggers, flows, and processes in the same transaction share the same limit, so the headroom is even smaller.

**Anti-pattern:**

```apex
trigger CaseTrigger on Case (before insert, before update) {
    for (Case c : Trigger.new) {
        Account a = [SELECT Id, Name, Industry FROM Account WHERE Id = :c.AccountId];
        if (a.Industry == 'Banking') {
            c.Priority = 'High';
        }
    }
}
```

**Bulkified rewrite:**

```apex
trigger CaseTrigger on Case (before insert, before update) {
    // 1. Collect all IDs
    Set<Id> accountIds = new Set<Id>();
    for (Case c : Trigger.new) {
        if (c.AccountId != null) {
            accountIds.add(c.AccountId);
        }
    }

    // 2. One query, outside the loop
    Map<Id, Account> accountMap = new Map<Id, Account>(
        [SELECT Id, Name, Industry FROM Account WHERE Id IN :accountIds]
    );

    // 3. Loop and use the map
    for (Case c : Trigger.new) {
        Account a = accountMap.get(c.AccountId);
        if (a != null && a.Industry == 'Banking') {
            c.Priority = 'High';
        }
    }
}
```

**Key points:** collect IDs, query once with `IN :set`, store results in a `Map`, then look up by key in the loop. Best practice is also to move the logic into a handler class, keeping the trigger thin.