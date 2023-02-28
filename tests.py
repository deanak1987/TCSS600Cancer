list = []
for i in range(20):
    list.append(i)
print(list)
n = 3
trow = []
tcol = []
# for i in range(n):
#     trow.append([])
# print(trow)

def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))


trow = tuple(split(list, n))
tcol = tuple(split(list, n))
print(trow)
d = {}
x = 0
for i in range(n + 1):
    for j in range(n + 1):
        x = x + 1
        d["string{0}".format(x)] = [i,j]
print(d)