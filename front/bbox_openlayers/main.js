import "./style.css";
import MVT from "ol/format/MVT.js";
import Map from "ol/Map.js";
import VectorTileLayer from "ol/layer/VectorTile.js";
import VectorTileSource from "ol/source/VectorTile.js";
import View from "ol/View.js";
import { Fill, Icon, Stroke, Style, Text } from "ol/style.js";
import TextPlacement from "ol/style/Text.js";
import TileLayer from "ol/layer/Tile.js";
import { TileDebug } from "ol/source.js";

const rankStyle = new Style({
    text: new Text({
        font: 'bold 11px "Open Sans", "Arial Unicode MS", "sans-serif"',
        placement: "line",
        fill: new Fill({
            color: "red",
        }),
    }),
});

const cladeStyle = new Style({
    text: new Text({
        font: "23px Calibri,sans-serif",
        fill: new Fill({
            color: "blue",
        }),
        stroke: new Stroke({
            color: "#fff",
            width: 4,
        }),
    }),
});
const leaveStyle = new Style({
    text: new Text({
        font: "10px Calibri,sans-serif",
        fill: new Fill({
            color: "yellow",
        }),
    }),
});
const style = [rankStyle, cladeStyle, leaveStyle];

const eukaryotes_style = new Style({
    fill: new Fill({ color: "rgba(150, 150, 255, 0.3)" }),
});

const bacteria_style = new Style({
    fill: new Fill({ color: "rgba(255, 150, 150, 0.3)" }),
});

const archae_style = new Style({
    fill: new Fill({ color: "rgba(150, 255, 150, 0.3)" }),
});

// Carte
// -----
const map = new Map({
    layers: [
        // Layer polyeuk
        new VectorTileLayer({
            source: new VectorTileSource({
                maxZoom: 42,
                format: new MVT(),
                url: "https://lifemap-back.dev.lhst.eu/vector_tiles/xyz/poly/{z}/{x}/{y}.pbf",
            }),
            //opacity: 0.3,
            style: function (feature) {
                const ref = feature.getProperties().ref;
                if (ref == 2) {
                    return eukaryotes_style;
                }
                if (ref == 1) {
                    return archae_style;
                }
                if (ref == 3) {
                    return bacteria_style;
                }
                return null;
            },
        }),

        // Layer lines
        new VectorTileLayer({
            source: new VectorTileSource({
                maxZoom: 42,
                format: new MVT(),
                url: "https://lifemap-back.dev.lhst.eu/vector_tiles/xyz/lines/{z}/{x}/{y}.pbf",
            }),
        }),
        // Layer ranks (line)
        new VectorTileLayer({
            source: new VectorTileSource({
                maxZoom: 42,
                format: new MVT(),
                url: "https://lifemap-back.dev.lhst.eu/vector_tiles/xyz/ranks/{z}/{x}/{y}.pbf",
            }),
            style: new Style({
                stroke: new Stroke({
                    color: "red",
                    width: 1,
                }),
            }),
        }),
        // Layer ranks (text)
        new VectorTileLayer({
            declutter: true,
            source: new VectorTileSource({
                maxZoom: 42,
                format: new MVT(),
                url: "https://lifemap-back.dev.lhst.eu/vector_tiles/xyz/ranks/{z}/{x}/{y}.pbf",
            }),
            style: function (feature) {
                rankStyle.getText().setText(feature.get("rank"));
                // .setText([
                //   ` ${feature.get('rank')}`,
                //   '',
                //   '\n',
                //   '',
                // ]);
                // style.getText().setText(feature.get('name'));

                return style;
            },
        }),
        // Layer leaves (text)
        new VectorTileLayer({
            declutter: true,
            source: new VectorTileSource({
                maxZoom: 42,
                format: new MVT(),
                url: "https://lifemap-back.dev.lhst.eu/vector_tiles/xyz/leaves/{z}/{x}/{y}.pbf",
            }),
            style: function (feature) {
                leaveStyle
                    .getText()
                    .setText([` ${feature.get("sci_name")}`, "", "\n", ""]);
                return style;
            },
        }),
        // Layer clade (text)
        new VectorTileLayer({
            declutter: false,
            source: new VectorTileSource({
                maxZoom: 42,
                format: new MVT(),
                url: "https://lifemap-back.dev.lhst.eu/vector_tiles/xyz/clade/{z}/{x}/{y}.pbf",
            }),
            style: function (feature) {
                cladeStyle
                    .getText()
                    .setText([
                        ` ${feature.get("sci_name")}`,
                        `${feature.get("sqrzoom") / 5}px Calibri,sans-serif`,
                        `\n`,
                        "",
                        ` ${feature.get("common_name")}`,
                        "",
                    ]);
                return style;
            },
        }),
        // For debuging
        //    new TileLayer({
        //      source: new TileDebug(),
        //    }),
    ],
    target: "map",
    view: new View({
        center: [0, 0],
        zoom: 4,
        maxZoom: 42,
    }),
});
