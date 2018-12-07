def main(i, j, k):
	# El significado de cada valor de retorno se muestra:
	# 1: triángulo escaleno
	# 2: triángulo isósceles
	# 3: triángulo equilátero
	# 4: no es un triángulo

	#Validación de que los lados no son negativos
	#Sino, retorna 4
	if i <= 0 or j <= 0 or k <= 0:
		t = 4
		return t

	#Detecta lados de igual distancia
	t = 0
	if i == j:
		t = t + 1
	if i == k:
		t = t + 2
	if j == k:
		t = t + 3

	#Se valida de que se cumpla con la desigualdad triangular
	#antes de catalogarlo:
	if t == 0:
		if (i + j) <= k or (i + k) <= j or (j + k) <= i:
			t = 4
			return t
		else:
			t = 1
			return t

	#Finalmente, se determina el tipo de triángulo. En caso
	#que no cumpla con uno de los 3 tipos, no es un triángulo.
	if t > 3:
		t = 3
	elif t == 1 and (i + j) > k:
		t = 2
	elif t == 2 and (i + k) > j:
		t = 2
	elif t == 3 and (j + k) > i:
		t = 2
	else:
		t = 4

	return t

if __name__ == "__main__":
	main(4, 10, 10)
