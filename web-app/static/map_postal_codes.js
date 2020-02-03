var map = L.map("map").setView([36.6782395,-76.0781193], 10); // TODO: hardcoded
var map_data = null;

var postal_code_boundary = null;

var initMap = function() {
    $.ajax({
        dataType: "json",
        url: "/static/va.json",//gis[city_].postal_codes,
        success: function (data) {

            postal_code_boundary = new L.geoJson(data, {
                style: style,
                onEachFeature: onEachFeature
            });
            postal_code_boundary.addTo(map);

            map_data = data;
        }
    });
}

var loadArticleCounts = function(city) {
    console.log("Loading Counts for: " + city);

    getCountByPostalCode(city).then(function (counts) {
        if (counts) {

            counts.map(function(count) {
                postal_code_boundary.eachLayer(function(layer) {
                    //console.log(layer.feature.properties.ZCTA5CE10);
                    if (layer.feature.properties.ZCTA5CE10 == count[0]) {
                        var color = getColor(count[1]);
                        //console.log(color);
                        layer.setStyle({fillColor: color});
                        layer.feature.properties.count = count[1];
                        layer.feature.properties.color = color;
                    }
                });
            });

        }
    });
    return true;
}


function getColor(d) {
    //console.log(d);
    
    return d>=5000 ? '#990000' : 
        d >4000 ? '#a31919' :
        d > 3000 ? '#ad3232' :
        d > 2000 ? '#b74c4c' :
        d > 1000 ? '#c16666' :
        d > 500 ? '#cc7f7f' :
        d > 400 ? '#d69999' :
        d > 300 ? '#e0b2b2' :
        d > 50 ? '#eacccc' :
        d > 10 ? '#f4e5e5' :
        d > 5 ? '#eee5e5' :
        '#eeeeee';
}

function style(feature) {
    return {
        fillColor: feature.properties.color ? feature.properties.color : "white",
        weight: 2,
        opacity: 1,
        color: 'white',
        dashArray: '3',
        fillOpacity: 0.7
    };
}

L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=\'' + mapbox_key + '\'', {
    id: 'mapbox.light'
}).addTo(map);

var legend = L.control({position: 'bottomright'});

legend.onAdd = function (map) {

    var div = L.DomUtil.create('div', 'info legend');
    var grades = [0, 10, 50, 300, 400, 500, 1000, 2000, 3000, 4000, 5000];

    // loop through our density intervals and generate a label with a colored square for each interval
    for (var i = 0; i < grades.length; i++) {
        div.innerHTML +=
            '<i style="background:' + getColor(grades[i] + 1) + '"></i> ' +
            grades[i] + (grades[i + 1] ? '&ndash;' + grades[i + 1] + '<br>' : '+');
    }

    return div;
};

legend.addTo(map);

var info = L.control();

info.onAdd = function (map) {
    this._div = L.DomUtil.create('div', 'info'); // create a div with a class "info"
    this.update();
    return this._div;
};

// method that we will use to update the control based on feature properties passed
info.update = function (props) {
    if (!props) return;
    var count = props.count ? props.count : 0;
    var postal_code = props.ZCTA5CE10 ? props.ZCTA5CE10 : props.ZIP_CODE ? props.ZIP_CODE : props.ZIP;
    this._div.innerHTML = '<h4>Articles by Postal Code</h4>' +  (props ?
        '<b>Postal Code: ' + postal_code + '<br />' + count + ' articles</b>'
        : '');
};

info.addTo(map);

function highlightFeature(e) {
    var layer = e.target;

    layer.setStyle({
        weight: 3,
        color: '#339',
        dashArray: '',
        fillOpacity: 0.7
    });

    if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
        layer.bringToFront();
    }

    info.update(layer.feature.properties);
}

function resetHighlight(e) {
    if (postal_code_boundary)
    {
        postal_code_boundary.resetStyle(e.target);
        info.update();
    }  
}

function onEachFeature(feature, layer) {
    layer.on({
        mouseover: highlightFeature,
        mouseout: resetHighlight
    });
}


var getCountByPostalCode = function(city) {
   
    console.log("Getting count for: " + city);
    return new Promise((resolve, reject) => {
        d3.request("/api/postal-codes/" + city) // TODO: hardcoded URL
        .mimeType("application/json")
        .response(function (xhr) {
          return JSON.parse(xhr.responseText);
        })
        .get(function (error, data) {
          if (error) {
            console.error("Getting count for postal code");
            console.error(error);
            resolve(null);
          } else {
            resolve(data);
          }
    
        });
    });
  
}

