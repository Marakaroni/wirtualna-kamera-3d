# Wirtualna kamera 3D

Projekt z przedmiotu *Grafika komputerowa* (Politechnika Warszawska, 2026): wirtualna kamera poruszająca się po scenie złożonej z prostopadłościanów, napisana od zera — bez silnika 3D, tylko **Python + NumPy** (obliczenia) i **pygame** (rysowanie).

## Co jest zaimplementowane
- rzutowanie perspektywiczne z ogniskową (zoom)
- przesuwanie kamery w 6 kierunkach oraz obroty wokół osi X, Y, Z (macierze obrotu)
- **usuwanie niewidocznych powierzchni** — sortowanie ścian algorytmem malarskim z testami względem płaszczyzn ścian (`kamera.py`; `kamera_etap1.py` to wcześniejsza wersja szkieletowa)
- wczytywanie sceny z pliku `cuboids.txt`, zrzuty ekranu

## Uruchomienie
```bash
pip install -r requirements.txt
python kamera.py
```
Sterowanie: `W/S/A/D` — ruch, `Spacja/Shift` — góra/dół, strzałki oraz `Q/E` — obroty, `H/J` — zoom, `Esc` — wyjście.

Format `cuboids.txt`: w pierwszej linii liczba brył, potem po 8 wierzchołków `x y z` na bryłę (najpierw podstawa, potem górna ściana).
