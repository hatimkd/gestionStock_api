GESTIONSTOCK_API

DESCRIPTION
------------
GestionStock_API est une API RESTful développée avec Django REST Framework pour gérer les stocks, les articles, les commandes, les fournisseurs et les mouvements de stock.


PRÉREQUIS
----------
- Python 3.8 ou supérieur
- Git
- (Optionnel) Virtualenv pour isoler l'environnement


INSTALLATION
-------------
1. Clonez le dépôt :

    git clone https://github.com/ton-utilisateur/gestionStock_api.git
    cd gestionStock_api

2. (Optionnel) Créez et activez un environnement virtuel :

    Sur Windows :

        python -m venv venv
        venv\Scripts\activate

    Sur macOS / Linux :

        python3 -m venv venv
        source venv/bin/activate

3. Installez les dépendances :

    pip install -r requirements.txt


CONFIGURATION
--------------
Appliquez les migrations pour configurer la base de données :

    python manage.py migrate


LANCEMENT
----------
Lancez le serveur de développement :

    python manage.py runserver

L’API sera accessible à l’adresse : http://127.0.0.1:8000/


COMMANDES UTILES
-----------------
- Créer un superutilisateur :

    python manage.py createsuperuser

- Lancer les tests :

    python manage.py test


CONTRIBUTION
-------------
Les contributions sont bienvenues !
Merci de forker le projet, créer une branche et ouvrir une pull request.


LICENCE
--------
Ce projet est sous licence MIT.
Voir le fichier LICENSE pour plus de détails.
