def which_bucket(value: int, n: int) -> int:
    """Donne un numéro de bucket deterministe selon la valeur en entrée

    Args:
        value (int): Un entier
        n (int): Taille du bucket

    Returns:
        _type_: entier entre 0 et n
    """

    assert n > 1, "We need more than 1 bucket"

    for i in range(1, n):
        candidate = n - i
        rest = value % candidate

        if rest == 0:
            return candidate
    
    return 0