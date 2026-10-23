r"""
Tas binaire minimum (min-heap) implémenté à la main.

Le tas est rangé dans une simple liste Python. Pour l'élément à l'indice i :
  - son parent est à l'indice (i - 1) // 2
  - son enfant gauche est à l'indice 2 * i + 1
  - son enfant droit est à l'indice 2 * i + 2

Propriété du tas : chaque parent a une priorité <= à celle de ses enfants.
Conséquence : le plus petit élément est toujours à l'indice 0.

Exemple (priorités seulement) :

            1               liste : [1, 3, 2, 7, 4]
          /   \             indice : 0  1  2  3  4
         3     2
        / \
       7   4
"""


class MinHeap:
    def __init__(self):
        # Chaque case contient un couple (priorité, valeur).
        # Pour Dijkstra : priorité = distance, valeur = identifiant du sommet.
        self._data = []

    def __len__(self):
        return len(self._data)

    def is_empty(self):
        return len(self._data) == 0

    def push(self, priority, value):
        """Ajoute un élément puis le fait remonter à sa place. Complexité O(log n)."""
        self._data.append((priority, value))
        self._sift_up(len(self._data) - 1)

    def pop(self):
        """Retire et renvoie le couple (priorité, valeur) de plus petite priorité. O(log n)."""
        if self.is_empty():
            raise IndexError("pop sur un tas vide")
        # On échange la racine (le minimum) avec le dernier élément,
        # on retire le dernier (= l'ancien minimum), puis on fait
        # redescendre la nouvelle racine à sa place.
        last = len(self._data) - 1
        self._swap(0, last)
        smallest = self._data.pop()
        if self._data:
            self._sift_down(0)
        return smallest

    def peek(self):
        """Renvoie le minimum sans le retirer. O(1)."""
        if self.is_empty():
            raise IndexError("peek sur un tas vide")
        return self._data[0]

    def _sift_up(self, i):
        """Fait remonter l'élément i tant qu'il est plus petit que son parent."""
        while i > 0:
            parent = (i - 1) // 2
            if self._data[i][0] < self._data[parent][0]:
                self._swap(i, parent)
                i = parent
            else:
                break

    def _sift_down(self, i):
        """Fait descendre l'élément i tant qu'un de ses enfants est plus petit que lui."""
        n = len(self._data)
        while True:
            left = 2 * i + 1
            right = 2 * i + 2
            smallest = i
            if left < n and self._data[left][0] < self._data[smallest][0]:
                smallest = left
            if right < n and self._data[right][0] < self._data[smallest][0]:
                smallest = right
            if smallest == i:
                break
            self._swap(i, smallest)
            i = smallest

    def _swap(self, i, j):
        self._data[i], self._data[j] = self._data[j], self._data[i]
