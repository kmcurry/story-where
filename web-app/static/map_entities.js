var map;
        var heatmapLayer;
        var heatMapData = null;
        var iconUrl = 'http://icons.iconarchive.com/icons/mad-science/arcade-saturdays/32/Dot-icon.png';

        var availableCities = [
            'Chesapeake',
            'Hampton',
            'Norfolk',
            'Newport News',
            'Portsmouth',
            'Suffolk',
            'Virginia Beach',
            'Williamsburg'
        ]

        function clearMap() {
            heatmapLayer.setMap(null);
        }

        function initMap() {

            heatMapData = new google.maps.MVCArray([]);
            infowindow = new google.maps.InfoWindow();

            var hampton_roads = new google.maps.LatLng(36.6, -76.3637);

            map = new google.maps.Map(document.getElementById('map'), {
                center: hampton_roads,
                zoom: 9,
                styles: [{
                        elementType: 'geometry',
                        stylers: [{
                            color: '#242f3e'
                        }]
                    },
                    {
                        elementType: 'labels.text.stroke',
                        stylers: [{
                            color: '#242f3e'
                        }]
                    },
                    {
                        elementType: 'labels.text.fill',
                        stylers: [{
                            color: '#746855'
                        }]
                    },
                    {
                        featureType: 'administrative.locality',
                        elementType: 'labels.text.fill',
                        stylers: [{
                            color: '#d59563'
                        }]
                    },
                    {
                        featureType: 'poi',
                        elementType: 'labels.text.fill',
                        stylers: [{
                            color: '#d59563'
                        }]
                    },
                    {
                        featureType: 'poi.park',
                        elementType: 'geometry',
                        stylers: [{
                            color: '#263c3f'
                        }]
                    },
                    {
                        featureType: 'poi.park',
                        elementType: 'labels.text.fill',
                        stylers: [{
                            color: '#6b9a76'
                        }]
                    },
                    {
                        featureType: 'road',
                        elementType: 'geometry',
                        stylers: [{
                            color: '#38414e'
                        }]
                    },
                    {
                        featureType: 'road',
                        elementType: 'geometry.stroke',
                        stylers: [{
                            color: '#212a37'
                        }]
                    },
                    {
                        featureType: 'road',
                        elementType: 'labels.text.fill',
                        stylers: [{
                            color: '#9ca5b3'
                        }]
                    },
                    {
                        featureType: 'road.highway',
                        elementType: 'geometry',
                        stylers: [{
                            color: '#746855'
                        }]
                    },
                    {
                        featureType: 'road.highway',
                        elementType: 'geometry.stroke',
                        stylers: [{
                            color: '#1f2835'
                        }]
                    },
                    {
                        featureType: 'road.highway',
                        elementType: 'labels.text.fill',
                        stylers: [{
                            color: '#f3d19c'
                        }]
                    },
                    {
                        featureType: 'transit',
                        elementType: 'geometry',
                        stylers: [{
                            color: '#2f3948'
                        }]
                    },
                    {
                        featureType: 'transit.station',
                        elementType: 'labels.text.fill',
                        stylers: [{
                            color: '#d59563'
                        }]
                    },
                    {
                        featureType: 'water',
                        elementType: 'geometry',
                        stylers: [{
                            color: '#17263c'
                        }]
                    },
                    {
                        featureType: 'water',
                        elementType: 'labels.text.fill',
                        stylers: [{
                            color: '#515c6d'
                        }]
                    },
                    {
                        featureType: 'water',
                        elementType: 'labels.text.stroke',
                        stylers: [{
                            color: '#17263c'
                        }]
                    }
                ]
            });

            heatmapLayer = new google.maps.visualization.HeatmapLayer({
                data: heatMapData,
                radius: 20,
                opacity: 0.8
            });
            heatmapLayer.setMap(map);

            getMoreEntities(0);
        }

        function mapSection() {
            console.log($("#section-search").val());
            clearMap();
        }

        function appendEntity(entity, page) {
            var entitiesList = document.getElementById("entitiesList");
            var li = document.createElement("li");
            var p = document.createElement("p");
            var a = document.createElement("a");
            var text = document.createTextNode(entity['entity']);
            var small = document.createElement("small");
            var smallText = document.createTextNode(entity['article_count'] + " articles");
            var method = "mapArticles('" + JSON.stringify(entity) + "')";
            a.setAttribute("onclick", method);
            a.appendChild(text);
            small.appendChild(smallText);
            p.appendChild(a);
            p.appendChild(document.createElement("br"));
            p.appendChild(small);
            li.appendChild(p);
            entitiesList.appendChild(li);

            if (entity['location']['lat'] > 36.5 && entity['location']['lat'] < 37.2 && entity['location']['lng'] > -
                77 && entity['location']['lng'] < -75.5) {
                heatMapData.push({
                    "location": new google.maps.LatLng(entity['location']['lat'], entity['location']['lng'])
                });
            }

            //mark(entity.location, entity.entity, true);
        }

        function getMoreEntities(page) {

            console.log("fetching more entities")


            var xhttp = new XMLHttpRequest();
            xhttp.onreadystatechange = function () {
                if (this.readyState == 4 && this.status == 200) {

                    var entities = JSON.parse(xhttp.responseText);

                    if (entities.length == 0) {
                        var msg = "The server is returning 200 but there are no entities. \
                        This can happen when the database is being repopulated."
                        console.log(msg)

                        var entitiesList = document.getElementById("entitiesList");
                        var text = document.createTextNode(msg);
                        entitiesList.appendChild(text);
                    }

                    entities.forEach(entity => appendEntity(entity, page));

                }

            };
            xhttp.open("GET", "/api/entities/" + page + "/1000", true);
            xhttp.send();
        }

        var articleMarkers = [];
        var infowindow;

        function getInfoWindowClickHandler(marker, location) {
            return function () {
                infowindow.setContent(location.name);
                infowindow.open(map, marker);
            }
        }

        function mapArticle(articleId) {
            $("#cur-num-article").html(curArticle + 1);
            $("#article-title").html("LOADING...");
            $("#article-date").html("");
            $("#article-body").html("");
            $("#article-locations-list").html("");
            $("#article-entities-list").html("");

            articleMarkers.forEach(m => m.setMap(null));

            $.get("/api/article/" + articleId)
                .done(function (article) {

                    var bounds = new google.maps.LatLngBounds();
                    var locations = article.nl_entities.filter(nle => nle.type == "LOCATION" && nle.location !=
                        null);
                    locations.forEach(location => {
                        var marker = mark(location.location, location.name, false);
                        marker.addListener('click', getInfoWindowClickHandler(marker, location));
                        bounds.extend(marker.getPosition());
                        articleMarkers.push(marker);
                    });
                    map.fitBounds(bounds);

                    $("#article-title").html(article.headline);
                    $("#article-date").html(article.release_date);
                    $("#article-body").html(article.body.replace(/\|/g, '<br>'));

                    article.nl_entities.forEach(entity => {
                        var list = "";
                        if (entity.location)
                            list = "#article-locations-list";
                        else
                            list = "#article-entities-list";
                        $(list).append("<div>" + entity.name +
                            "</div><div class=\"text-muted small mb-1\">" + entity.type + " - " + (
                                entity.salience.toString().substring(0, 5)) + "</div>");
                    });
                });
        }

        var curArticle = -1;
        var articleIds = [];

        function mapArticles(entity) {
            entity = JSON.parse(entity);
            $("#cur-entity-name").html(entity.entity);

            articleIds = entity['article_ids'];
            curArticle = -1;
            $("#total-num-articles").html(articleIds.length);

            $("#entities").hide();
            $("#article").show();

            curArticle += 1;
            mapArticle(articleIds[curArticle]);
        }

        function mark(location, title, icon) {
            //console.log(location.lat + ", " + location.lng);
            var myLatLng = {
                lat: location.lat,
                lng: location.lng
            };

            var marker = new google.maps.Marker({
                position: myLatLng,
                map: map,
                title: title
            });

            if (icon) {
                marker.setIcon({
                    path: google.maps.SymbolPath.CIRCLE,
                    fillColor: '#00F',
                    fillOpacity: 0.8,
                    strokeColor: '#00A',
                    strokeOpacity: 1,
                    strokeWeight: 1,
                    scale: 3
                });
            }

            return marker;
        }

        function showArticles(entity) {
            console.log("Showing Articles for Entity: " + entity);
        }