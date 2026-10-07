Bomberman Neon Edition

O implementare în Python și Pygame a clasicului joc Bomberman, extinsă cu efecte grafice dinamice, mecanică de profil, magazin de upgrade-uri și opțiuni de joc în doi jucători locali sau contra unui bot. Proiectul a fost dezvoltat ca parte a portofoliului personal de programare și dezvoltare de jocuri 2D.

Functionalitati

Multiplayer local (1v1) si Bot AI:

Doi jucatori umani pe aceeasi tastatura.

Suport pentru boti controlati de un algoritm simplu de decizie si plasare de bombe.

Selectie si generare de harti:

Harti predefinite: Clasic si Retro Arcade.

Generator procedural de harti (Aleatoriu), care asigura zone libere la colturi pentru aparitia jucatorilor.

Mecanici de joc:

Distrugere de pereti moi cu generare de particule si screen-shake la explozii.

Reactii in lant ale bombelor.

Scut temporar activabil o data pe runda.

Modul Spirala Mortii (Sudden Death): dupa 45 de secunde, marginile hartii incep sa se blocheze progresiv in spirala.

Sistem de bonusuri (Power-ups):

Viata suplimentara (+1 HP).

Raza extinsa pentru flacara bombei (+1 Raza).

Capacitate marita de bombe plasate simultan (+1 Bomba).

Crestere de viteza (+Viteza).

Profil si Progresie:

Autentificare locala pe baza de nume de utilizator.

Nivel, XP si bani obtinuti prin distrugerea peretilor si eliminarea adversarilor.

Salvare automata a progresului in fisier JSON (profiles.json).

Magazin in joc unde se pot achizitiona permanent upgrade-uri de raza si numar de bombe pentru ambii jucatori.

Stil vizual si sunet:

Iluminare dinamica circulara (blend mode peste o masca ambientala de noapte).

Sprite-sheet modular cu selectie de personaje si culori custom.

Efecte sonore pentru plasare, explozie si eliminare (cu fallback automat daca nu exista placa audio activa).

Cerinte de sistem

Python: versiunea 3.8 sau mai noua.

Pygame: biblioteca externa necesara pentru grafica, input si sunet.

Instalare si Rulare

Clonati acest depozit sau descarcati fisierele sursa:

git clone https://github.com/utilizator/bomberman-neon.git
cd bomberman-neon


Instalati dependintele:

pip install pygame


Asigurati-va ca aveti fisierele de resurse in acelasi director cu scriptul:

Bombermannn.png (obligatoriu - sprite sheet)

place.wav, explode.wav, die.wav (optionale - efecte audio)

Porniti jocul:

python bomberman.py


Controale

Jucatorul 1 (P1)

W, A, S, D: Deplasare (Sus, Stanga, Jos, Dreapta)

F: Plasare bomba

E: Activare scut temporar (5 secunde)

Jucatorul 2 (P2)

Sageti: Deplasare

ENTER: Plasare bomba

Right Shift: Activare scut temporar (5 secunde)

Comenzi Generale

SPACE: Pauza / Reluare joc

R / ESC: Revenire la meniul principal (salveaza automat profilul)

Structura Proiectului

bomberman.py: Contine logica intregului joc (bucle, fizica coliziunilor, render, GUI meniuri).

profiles.json: Fisier generat automat la rulare pentru persistenta datelor utilizatorilor.

Bombermannn.png: Textura pentru caractere.

Audio: fisierele .wav pentru interactiuni sonore.

Posibile Imbunatatiri Viitoare

Suport pentru multiplayer in retea prin socket-uri TCP/UDP.

Imbunatatirea algoritmului botului prin cautare de drum (A* pathfinding).

Adaugarea de obstacole mobile si noi tipuri de bombe (ex. teleghidate, mine).
