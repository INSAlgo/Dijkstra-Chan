def dist(str1, str2) :
    l1, l2 = len(str1), len(str2)
    arr = [[j for j in range(l2+1)]]
    arr += [[i] + [0 for _ in range(l2)] for i in range(1, l1+1)]

    for i in range(1, l1 + 1) :
        for j in range(1, l2 + 1) :
            m = min(arr[i-1][j-1], arr[i][j-1], arr[i-1][j])
            if str1[i-1] == str2[j-1] :
                arr[i][j] = m
            else :
                arr[i][j] = m + 1
    
    return arr[l1][l2]