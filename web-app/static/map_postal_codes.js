var mapbox_key = $("#mapbox_key").val();;
var map = L.map("map").setView([36.6782395,-76.0781193], 10); // TODO: hardcoded


var postal_code_boundary = null;

// var data = $("#data").val();
// data = JSON.parse(data);


function getColor(d) {
    //console.log(d);
    
    return d>=3000 ? '#990000' : 
        d >2000 ? '#d7301f' :
        d > 1500 ? '#ef6548' :
        d > 500 ? '#fc8d59' :
        d > 100 ? '#fdbb84' :
        d > 10 ? '#fdd49e' :
        '#eeeeee';
}

function style(feature) {
    //console.log(feature.properties.count)
    var fill = getColor(feature.properties.count);
    //console.log("Fill Color: " + fill);
    return {
        fillColor: fill,
        weight: 2,
        opacity: 1,
        color: 'white',
        dashArray: '3',
        fillOpacity: 0.7
    };
}

L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=' + mapbox_key, {
    id: 'mapbox.light'
}).addTo(map);

var legend = L.control({position: 'bottomright'});

legend.onAdd = function (map) {

    var div = L.DomUtil.create('div', 'info legend');
    var grades = [0, 10, 100, 500, 1500, 2000, 3000];

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
    var count = props && props.count ? props.count : 0;
    this._div.innerHTML = '<h4>Articles by Postal Code</h4>' +  (props ?
        '<b>Postal Code: ' + props.ZIP_CODE + '<br />' + count + ' articles</b>'
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
        d3.request("http://localhost:8080/api/postal-codes/" + city)
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

$.ajax({
    dataType: "json",
    //url: "https://gis.data.vbgov.com/datasets/759ad66064974eab9a556d3a90efa1a1_23.geojson", // TODO: hard coded
    url: "https://opendata.arcgis.com/datasets/82ada480c5344220b2788154955ce5f0_1.geojson",
    success: function (data) {

        var city = "Virginia Beach" // TODO: hard coded
        getCountByPostalCode(city).then(function (counts) {
            if (counts) {
                //console.log(data);

                data.features.forEach(function (feature, index) {
                    var articlesInPostalCode = counts.map(function(count) {
                        //console.log(count[1]);
                        return count[1];
                    })
                    //console.log(articlesInPostalCode);
                    feature.properties.count = articlesInPostalCode[index];
                });
                
                postal_code_boundary = new L.geoJson(data, {
                    style: style,
                    onEachFeature: onEachFeature
                });
                postal_code_boundary.addTo(map);
            }
        });
    }
});
