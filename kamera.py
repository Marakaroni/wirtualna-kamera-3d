import pygame
import numpy as np
import math
import sys
from functools import cmp_to_key
from datetime import datetime


class Camera:
    def __init__(self):
        self.pozycja = np.array([-4.0, 3.0, 2.0])

        self.obrot_x = 0.0
        self.obrot_y = math.radians(90.0)
        self.obrot_z = 0.0

        self.orientacja = (
            self._macierz_obrotu_x(self.obrot_x)
            @ self._macierz_obrotu_y(self.obrot_y)
            @ self._macierz_obrotu_z(self.obrot_z)
        )

        self.ogniskowa = 500.0

    def pobierz_macierz_widoku(self):
        return self.orientacja.T

    def transformuj_wierzcholek(self, wierzcholek):
        w_kamerze = wierzcholek - self.pozycja
        w_kamerze = self.orientacja.T @ w_kamerze
        return w_kamerze

    def rzutuj_wierzcholek(self, wierzcholek_3d):
        x, y, z = wierzcholek_3d

        if z <= 0.1:
            return None

        ekran_x = (x / z) * self.ogniskowa
        ekran_y = (y / z) * self.ogniskowa

        return (ekran_x, ekran_y)

    def ruch_do_przodu(self, odleglosc):
        kierunek = self._kierunek_do_przodu()
        self.pozycja += kierunek * odleglosc

    def ruch_do_tylu(self, odleglosc):
        kierunek = self._kierunek_do_przodu()
        self.pozycja -= kierunek * odleglosc

    def ruch_w_lewo(self, odleglosc):
        kierunek = self._kierunek_w_prawo()
        self.pozycja -= kierunek * odleglosc

    def ruch_w_prawo(self, odleglosc):
        kierunek = self._kierunek_w_prawo()
        self.pozycja += kierunek * odleglosc

    def ruch_w_gore(self, odleglosc):
        kierunek = self._kierunek_w_gore()
        self.pozycja += kierunek * odleglosc

    def ruch_w_dol(self, odleglosc):
        kierunek = self._kierunek_w_gore()
        self.pozycja -= kierunek * odleglosc

    def _kierunek_do_przodu(self):
        return self.orientacja @ np.array([0, 0, -1])

    def _kierunek_w_prawo(self):
        return self.orientacja @ np.array([1, 0, 0])

    def _kierunek_w_gore(self):
        return self.orientacja @ np.array([0, 1, 0])

    def obroc_x(self, kat):
        self.obrot_x += kat
        self.orientacja = self.orientacja @ self._macierz_obrotu_x(kat)

    def obroc_y(self, kat):
        self.obrot_y += kat
        self.orientacja = self.orientacja @ self._macierz_obrotu_y(kat)

    def obroc_z(self, kat):
        self.obrot_z += kat
        self.orientacja = self.orientacja @ self._macierz_obrotu_z(kat)

    def _macierz_obrotu_x(self, kat):
        return np.array([
            [1, 0, 0],
            [0, math.cos(kat), -math.sin(kat)],
            [0, math.sin(kat), math.cos(kat)]
        ])

    def _macierz_obrotu_y(self, kat):
        return np.array([
            [math.cos(kat), 0, math.sin(kat)],
            [0, 1, 0],
            [-math.sin(kat), 0, math.cos(kat)]
        ])

    def _macierz_obrotu_z(self, kat):
        return np.array([
            [math.cos(kat), -math.sin(kat), 0],
            [math.sin(kat), math.cos(kat), 0],
            [0, 0, 1]
        ])

    def przybliz(self, wspolczynnik):
        self.ogniskowa *= wspolczynnik

    def oddal(self, wspolczynnik):
        self.ogniskowa /= wspolczynnik


class Cuboid:
    def __init__(self, wierzcholki):
        self.wierzcholki = [np.array(w, dtype=float) for w in wierzcholki]
        self.srodek = np.mean(self.wierzcholki, axis=0)
        self.sciany = [
            (0, 1, 2, 3),
            (4, 5, 6, 7),
            (0, 1, 5, 4),
            (1, 2, 6, 5),
            (2, 3, 7, 6),
            (3, 0, 4, 7)
        ]

    def rzutuj_wierzcholki(self, kamera):
        rzuty = []
        for wierzcholek in self.wierzcholki:
            w_kamerze = kamera.transformuj_wierzcholek(wierzcholek)
            w_2d = kamera.rzutuj_wierzcholek(w_kamerze)
            rzuty.append(w_2d)
        return rzuty


def wczytaj_prostopadlosciany(nazwa_pliku):
    prostopadlosciany = []
    with open(nazwa_pliku, 'r') as plik:
        liczba_prostopadloscianow = int(plik.readline().strip())
        for _ in range(liczba_prostopadloscianow):
            wierzcholki = []
            for _ in range(8):
                wspolrzedne = list(map(float, plik.readline().strip().split()))
                wierzcholki.append(wspolrzedne)
            prostopadlosciany.append(Cuboid(wierzcholki))
    return prostopadlosciany


def _klasyfikuj_sciane_wzgledem_plaszczyzny(testowe_wierzcholki, punkt_plaszczyzny, normalna_plaszczyzny, eps=1e-6):
    odleglosci = [float(np.dot(normalna_plaszczyzny, w - punkt_plaszczyzny)) for w in testowe_wierzcholki]
    if all(odleglosc > eps for odleglosc in odleglosci):
        return 1
    if all(odleglosc < -eps for odleglosc in odleglosci):
        return -1
    return 0



def _strona_obserwatora(sciana, eps=1e-6):
    wartosc_strony = float(np.dot(sciana["normalna_plaszczyzny"], -sciana["punkt_plaszczyzny"]))
    if abs(wartosc_strony) <= eps:
        return 0
    return 1 if wartosc_strony > 0 else -1


def _test3_b_po_przeciwnej_stronie_obserwatora_wzgledem_plaszczyzny_a(sciana_a, sciana_b, eps=1e-6):
    strona_b = _klasyfikuj_sciane_wzgledem_plaszczyzny(
        sciana_b["wierzcholki_kamera"],
        sciana_a["punkt_plaszczyzny"],
        sciana_a["normalna_plaszczyzny"],
        eps
    )
    if strona_b == 0:
        return False

    strona_obserwatora_a = _strona_obserwatora(sciana_a, eps)
    if strona_obserwatora_a == 0:
        return False

    return strona_b == -strona_obserwatora_a


def _test4_a_po_tej_samej_stronie_co_obserwator_wzgledem_plaszczyzny_b(sciana_a, sciana_b, eps=1e-6):
    strona_a = _klasyfikuj_sciane_wzgledem_plaszczyzny(
        sciana_a["wierzcholki_kamera"],
        sciana_b["punkt_plaszczyzny"],
        sciana_b["normalna_plaszczyzny"],
        eps
    )
    if strona_a == 0:
        return False

    strona_obserwatora_b = _strona_obserwatora(sciana_b, eps)
    if strona_obserwatora_b == 0:
        return False

    return strona_a == strona_obserwatora_b


def _wykonaj_testy_1_do_4(sciana_a, sciana_b, eps=1e-6):
    #Testów 1 i 2 nie implementuje na razie.

    if _test3_b_po_przeciwnej_stronie_obserwatora_wzgledem_plaszczyzny_a(sciana_a, sciana_b, eps):
        return "b_za_a"

    if _test4_a_po_tej_samej_stronie_co_obserwator_wzgledem_plaszczyzny_b(sciana_a, sciana_b, eps):
        return "b_za_a"

    return "nierozstrzygniete"


def _wykonaj_testy_3_i_4(sciana_a, sciana_b, eps=1e-6):
    if _test3_b_po_przeciwnej_stronie_obserwatora_wzgledem_plaszczyzny_a(sciana_a, sciana_b, eps):
        return "b_za_a"
    if _test4_a_po_tej_samej_stronie_co_obserwator_wzgledem_plaszczyzny_b(sciana_a, sciana_b, eps):
        return "b_za_a"
    return "nierozstrzygniete"


def _awaryjny_porzadek_glebokosci(sciana_a, sciana_b, eps=1e-6):
    if abs(sciana_a["srednie_z"] - sciana_b["srednie_z"]) > eps:
        return -1 if sciana_a["srednie_z"] > sciana_b["srednie_z"] else 1
    return sciana_a["id_kolejnosci"] - sciana_b["id_kolejnosci"]


def porownaj_sciany(sciana_a, sciana_b):
    wynik_ab = _wykonaj_testy_1_do_4(sciana_a, sciana_b)
    if wynik_ab == "b_za_a":
        return 1
    if wynik_ab == "brak_zaslaniania":
        return _awaryjny_porzadek_glebokosci(sciana_a, sciana_b)

    wynik_ba = _wykonaj_testy_3_i_4(sciana_b, sciana_a)
    if wynik_ba == "b_za_a":
        return -1

    return _awaryjny_porzadek_glebokosci(sciana_a, sciana_b)


def uruchom():
    pygame.init()

    szerokosc_okna, wysokosc_okna = 1200, 900
    ekran = pygame.display.set_mode((szerokosc_okna, wysokosc_okna))
    pygame.display.set_caption("Grafika Komputerowa - Wirtualna Kamera")
    zegar = pygame.time.Clock()

    kamera = Camera()
    prostopadlosciany = wczytaj_prostopadlosciany('cuboids.txt')

    predkosc_ruchu = 0.1
    predkosc_obrotu = 0.025
    wspolczynnik_zoom = 1.05

    czy_dziala = True
    while czy_dziala:
        for zdarzenie in pygame.event.get():
            if zdarzenie.type == pygame.QUIT:
                czy_dziala = False
            if zdarzenie.type == pygame.KEYDOWN:
                if zdarzenie.key == pygame.K_ESCAPE:
                    czy_dziala = False
                if zdarzenie.key == pygame.K_l:
                    zapisz_zrzut_ekranu(ekran)

        klawisze = pygame.key.get_pressed()

        if klawisze[pygame.K_w]:
            kamera.ruch_do_tylu(predkosc_ruchu)
        if klawisze[pygame.K_s]:
            kamera.ruch_do_przodu(predkosc_ruchu)
        if klawisze[pygame.K_a]:
            kamera.ruch_w_lewo(predkosc_ruchu)
        if klawisze[pygame.K_d]:
            kamera.ruch_w_prawo(predkosc_ruchu)

        if klawisze[pygame.K_LSHIFT] or klawisze[pygame.K_RSHIFT]:
            kamera.ruch_w_dol(predkosc_ruchu)
        if klawisze[pygame.K_SPACE]:
            kamera.ruch_w_gore(predkosc_ruchu)

        if klawisze[pygame.K_UP]:
            kamera.obroc_x(-predkosc_obrotu)
        if klawisze[pygame.K_DOWN]:
            kamera.obroc_x(predkosc_obrotu)
        if klawisze[pygame.K_LEFT]:
            kamera.obroc_y(-predkosc_obrotu)
        if klawisze[pygame.K_RIGHT]:
            kamera.obroc_y(predkosc_obrotu)

        if klawisze[pygame.K_q]:
            kamera.obroc_z(predkosc_obrotu)
        if klawisze[pygame.K_e]:
            kamera.obroc_z(-predkosc_obrotu)

        if klawisze[pygame.K_h]:
            kamera.przybliz(wspolczynnik_zoom)
        if klawisze[pygame.K_j]:
            kamera.oddal(wspolczynnik_zoom)

        ekran.fill((20, 20, 30))

        sciany_do_rysowania = []
        licznik_kolejnosci = 0
        for prostopadloscian in prostopadlosciany:
            wierzcholki_kamera = []
            rzuty = []
            for wierzcholek in prostopadloscian.wierzcholki:
                w_kamerze = kamera.transformuj_wierzcholek(wierzcholek)
                wierzcholki_kamera.append(w_kamerze)
                rzuty.append(kamera.rzutuj_wierzcholek(w_kamerze))
            srodek_prostopadloscianu_kamera = kamera.transformuj_wierzcholek(prostopadloscian.srodek)

            for indeks_sciany, sciana in enumerate(prostopadloscian.sciany):
                if any(rzuty[indeks] is None for indeks in sciana):
                    continue
                sciana_kamera = [wierzcholki_kamera[indeks] for indeks in sciana]
                srodek_sciany_kamera = sum(sciana_kamera) / len(sciana_kamera)
                w0, w1, w2 = sciana_kamera[0], sciana_kamera[1], sciana_kamera[2]
                normalna = np.cross(w1 - w0, w2 - w0)
                if np.dot(normalna, srodek_sciany_kamera - srodek_prostopadloscianu_kamera) < 0:
                    normalna = -normalna
                if np.dot(normalna, -srodek_sciany_kamera) <= 1e-6:
                    continue
                srednie_z = sum(wierzcholek[2] for wierzcholek in sciana_kamera) / len(sciana_kamera)
                rzut_sciany = [rzuty[indeks] for indeks in sciana]
                sciany_do_rysowania.append({
                    "srednie_z": srednie_z,
                    "indeks_sciany": indeks_sciany,
                    "rzut_sciany": rzut_sciany,
                    "wierzcholki_kamera": sciana_kamera,
                    "punkt_plaszczyzny": sciana_kamera[0],
                    "normalna_plaszczyzny": normalna,
                    "id_kolejnosci": licznik_kolejnosci
                })
                licznik_kolejnosci += 1

        sciany_do_rysowania.sort(key=cmp_to_key(porownaj_sciany))
        rysuj_sciany(ekran, sciany_do_rysowania, szerokosc_okna, wysokosc_okna)

        czcionka = pygame.font.Font(None, 24)
        teksty_info = [
            f"Pos: ({kamera.pozycja[0]:.2f}, {kamera.pozycja[1]:.2f}, {kamera.pozycja[2]:.2f})",
            f"Rot: X={math.degrees(kamera.obrot_x):.1f}° Y={math.degrees(kamera.obrot_y):.1f}° Z={math.degrees(kamera.obrot_z):.1f}°",
            f"Focal: {kamera.ogniskowa:.1f}",
            "WSAD: Move | Shift/Space: Up/Down | Arrows: Rotate XY | Q/E: Rotate Z | H/J: Zoom | L: Screenshot"
        ]

        for indeks, tekst in enumerate(teksty_info):
            powierzchnia_tekstu = czcionka.render(tekst, True, (200, 200, 200))
            ekran.blit(powierzchnia_tekstu, (10, 10 + indeks * 25))

        pygame.display.flip()
        zegar.tick(60)

    pygame.quit()
    sys.exit()


def zapisz_zrzut_ekranu(ekran):
    znacznik_czasu = datetime.now().strftime("%Y%m%d_%H%M%S")
    nazwa_pliku = f"screenshot_{znacznik_czasu}.png"
    pygame.image.save(ekran, nazwa_pliku)


def rysuj_osie(ekran, kamera, szerokosc, wysokosc):
    punkt_zero = np.array([0, 0, 0])

    punkty_osi = {
        'X': np.array([1, 0, 0]),
        'Y': np.array([0, 1, 0]),
        'Z': np.array([0, 0, 1])
    }

    kolory = {
        'X': (255, 0, 0),
        'Y': (0, 255, 0),
        'Z': (0, 0, 255)
    }

    srodek_x, srodek_y = szerokosc // 2, wysokosc // 2

    for os, punkt in punkty_osi.items():
        p1 = kamera.transformuj_wierzcholek(punkt_zero)
        p2 = kamera.transformuj_wierzcholek(punkt_zero + punkt * 2)

        p1_2d = kamera.rzutuj_wierzcholek(p1)
        p2_2d = kamera.rzutuj_wierzcholek(p2)

        if p1_2d and p2_2d:
            pygame.draw.line(
                ekran,
                kolory[os],
                (srodek_x + p1_2d[0], srodek_y - p1_2d[1]),
                (srodek_x + p2_2d[0], srodek_y - p2_2d[1]),
                2
            )


def rysuj_sciany(ekran, sciany, szerokosc, wysokosc):
    srodek_x, srodek_y = szerokosc // 2, wysokosc // 2
    kolory_scian = [
        (220, 80, 80),
        (80, 200, 120),
        (80, 140, 230),
        (230, 200, 80),
        (200, 90, 200),
        (80, 210, 210)
    ]

    for sciana in sciany:
        indeks_sciany = sciana["indeks_sciany"]
        rzut_sciany = sciana["rzut_sciany"]
        punkty_ekranu = [
            (srodek_x + punkt[0], srodek_y - punkt[1])
            for punkt in rzut_sciany
        ]
        kolor = kolory_scian[indeks_sciany % len(kolory_scian)]
        pygame.draw.polygon(ekran, kolor, punkty_ekranu)
        pygame.draw.polygon(ekran, (20, 20, 20), punkty_ekranu, 1)


if __name__ == "__main__":
    uruchom()
