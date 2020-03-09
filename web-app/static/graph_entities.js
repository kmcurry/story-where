var simulation = null;

function dragstarted(d) {
    if (!d3.event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(d) {
    d.fx = d3.event.x;
    d.fy = d3.event.y;
}

function dragended(d) {
    if (!d3.event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
}

var initGraph = function () {
    console.log("initializeing graph, getting entities")
    $.ajax({
        dataType: "json",
        url: "/api/entities/0/3", //gis[city_].postal_codes,
        success: function (entities) {

            //console.log(entities);
            var graph = {
                nodes: [],
                links: []
            };

            entities.forEach(function (entity) {
                nodes = graph.nodes;
                links = graph.links;
                nodes.push({
                    id: entity.entity
                });
                entity.article_ids.forEach(function (aid) {
                    if (nodes.indexOf(aid) === -1) {
                        nodes.push({
                            id: aid
                        });
                    }
                    links.push({
                        source: entity.entity,
                        target: aid,
                        value: 2
                    })
                })
                return;
            });

            console.log(links);


            var svg = d3.select("svg"),
                width = +svg.attr("width"),
                height = +svg.attr("height");

            var color = d3.scaleOrdinal(d3.schemeCategory20);

            simulation = d3.forceSimulation()
                .force("link", d3.forceLink().id(function (d) {
                    return d.id;
                }))
                .force("charge", d3.forceManyBody())
                .force("center", d3.forceCenter(width / 2, height / 2));

                var link = svg.append("g")
                .attr("class", "links")
                .selectAll("line")
                .data(graph.links)
                .enter().append("line")
                .attr("stroke-width", function (d) {
                    return Math.sqrt(d.value);
                });

            var node = svg.append("g")
                .attr("class", "nodes")
                .selectAll("g")
                .data(graph.nodes)
                .enter().append("g")

            var circles = node.append("circle")
                .attr("r", 5)
                .attr("fill", function (d) {
                    return color(d.group);
                })
                .call(d3.drag()
                    .on("start", dragstarted)
                    .on("drag", dragged)
                    .on("end", dragended));

            var lables = node.append("text")
                .text(function (d) {
                    return d.id;
                })
                .attr('x', 6)
                .attr('y', 3);

            node.append("title")
                .text(function (d) {
                    return d.id;
                });

            simulation
                .nodes(graph.nodes)
                .on("tick", ticked);

            simulation.force("link")
                .links(graph.links);

            function ticked() {
                link
                    .attr("x1", function (d) {
                        return d.source.x;
                    })
                    .attr("y1", function (d) {
                        return d.source.y;
                    })
                    .attr("x2", function (d) {
                        return d.target.x;
                    })
                    .attr("y2", function (d) {
                        return d.target.y;
                    });

                node
                    .attr("transform", function (d) {
                        return "translate(" + d.x + "," + d.y + ")";
                    })
            }


            console.log("graph initialized")
        }
    });
}