# Leçon 13 : un site rapide sur téléphone

Sources : `accelerer-son-site`, web.dev (Core Web Vitals), PageSpeed Insights (pagespeed.web.dev).

## Script

### Scène 1. Le client n'attend pas (environ 30 s)

**À l'écran** : un téléphone avec une page blanche qui charge, un compteur de secondes.

**Voix** : Trois secondes, quatre secondes, toujours une page blanche. Sur téléphone, en 4G, beaucoup de
clients n'attendent pas : ils reviennent à Google et cliquent sur le concurrent. Aujourd'hui, on mesure,
puis on corrige.

### Scène 2. Mesurer avec PageSpeed Insights (environ 60 s)

**À l'écran** : capture de la page publique PageSpeed Insights, l'onglet « Mobile » mis en avant.

**Voix** : Ouvrez PageSpeed Insights, un outil gratuit de Google, et collez l'adresse de votre page
d'accueil, puis de vos pages importantes. Regardez l'onglet « Mobile ». En haut, les données des vrais
visiteurs, quand Google en a assez. En dessous, un test avec une note et la liste des problèmes. Notez
les trois premières recommandations.

### Scène 3. Les trois signaux de Google (environ 45 s)

**À l'écran** : LCP, INP, CLS, avec leurs seuils « bons » : 2,5 s, 200 ms, 0,1.

**Voix** : Google regarde trois signaux. Le temps d'affichage du contenu principal : bon sous deux
secondes et demie. La réactivité quand on touche un bouton. Et la stabilité de la page : le bouton qui
bouge au moment de cliquer.

### Scène 4. Les corrections les plus rentables (environ 60 s)

**À l'écran** : six gestes, le premier en grand : « Alléger les images ».

**Voix** : Dans la plupart des petits sites, la première cause de lenteur, ce sont les photos trop
lourdes. Redimensionnez-les à leur taille d'affichage et enregistrez-les en WebP ou en JPEG compressé.
Ensuite : supprimez les extensions et scripts inutiles, activez le cache chez votre hébergeur, et limitez
les polices. Si la note reste mauvaise, le problème vient souvent du thème ou de l'hébergement : c'est le
moment de demander un avis technique.

### Scène 5. L'action de la leçon (environ 25 s)

**Voix** : Votre action : testez trois pages, notez leurs résultats sur mobile, et corrigez les photos
les plus lourdes.

**À l'écran** : la fiche action.

## Fiche action

| Page testée | Note mobile | 3 premières recommandations | Corrigé |
| --- | --- | --- | --- |
| Accueil | | | ☐ |
| | | | ☐ |
| | | | ☐ |
