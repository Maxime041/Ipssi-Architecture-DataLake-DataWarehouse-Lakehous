import sys, os
ROOT = sys.argv[1]
def rows(j, t):
    p = os.path.join(ROOT, j, t, t + '.dat')
    with open(p, encoding='utf-8') as f:
        for l in f: yield l.rstrip('\r\n').split('|')
def ks(j, t, c=0): return {r[c] for r in rows(j, t)}

# 1. coherence data seul : faits data vs dimensions data seules
item_d, cust_d, addr_d = ks('data', 'item'), ks('data', 'customer'), ks('data', 'customer_address')
for t, c, s, name in [('inventory', 1, item_d, 'item'), ('store_sales', 2, item_d, 'item'), ('web_sales', 3, item_d, 'item'),
                      ('web_clickstreams', 3, item_d, 'item'), ('item_marketprices', 1, item_d, 'item'),
                      ('product_reviews', 4, item_d, 'item'), ('store_sales', 3, cust_d, 'customer'),
                      ('web_clickstreams', 5, cust_d, 'customer'), ('customer', 4, addr_d, 'customer_address')]:
    n = o = 0
    for r in rows('data', t):
        v = r[c]
        if v == '': continue
        n += 1
        if v not in s: o += 1
    print(f'DATA-SEUL {t}.{c} -> {name}: {o} orphelins / {n}')

# 2. clics et avis : commande web ou ticket magasin ?
ws = {(r[17], r[3]) for j in ('data', 'data_refresh') for r in rows(j, 'web_sales')}
ss = {(r[9], r[2]) for j in ('data', 'data_refresh') for r in rows(j, 'store_sales')}
for t, kc, ic in [('web_clickstreams', 2, 3), ('product_reviews', 6, 4)]:
    n = a = b = 0
    for r in rows('data', t):
        if r[kc] == '': continue
        n += 1; k = (r[kc], r[ic])
        a += k in ws; b += k in ss
    print(f'{t}: {n} lignes avec cle ; (commande,produit) trouve dans web_sales: {a} ; dans store_sales: {b}')

# 3. retours du refresh sans vente : exemples
ss_t = {r[9] for j in ('data', 'data_refresh') for r in rows(j, 'store_sales')}
tk = [r[9] for r in rows('data_refresh', 'store_returns')]
print('refresh store_returns tickets min/max', min(map(int, tk)), max(map(int, tk)), 'ticket existe:', sum(t in ss_t for t in tk), '/', len(tk))
