import "./style.css";
import MVT from "ol/format/MVT.js";
import Map from "ol/Map.js";
import VectorTileLayer from "ol/layer/VectorTile.js";
import VectorTileSource from "ol/source/VectorTile.js";
import View from "ol/View.js";
import { Fill, Stroke, Style, Text } from "ol/style.js";
import { Vector, TileDebug } from "ol/source.js";
import VectorLayer from "ol/layer/Vector.js";
import { fromLonLat, toLonLat } from "ol/proj";
import Feature from "ol/Feature.js";
import Point from "ol/geom/Point.js";
import { getBottomLeft, getTopRight } from "ol/extent.js";

const API_URL = "https://lifemap-back.dev.lhst.eu/solr";
const TEXT_COLOR = "rgba(255, 255, 255, 1)";
const TEXT_STROKE_COLOR = "rgba(0, 0, 0, 1)";

const label_style_function = (feature) => {
    const label_style = new Style({
        // image: new Circle({
        //     radius: 4,
        //     fill: new Fill({ color: "rgba(255, 255, 255, 1)" }),
        //     stroke: new Stroke({
        //         width: 1,
        //         color: "rgba(0, 0, 0, 1)",
        //     }),
        //     declutterMode: "none",
        //     zIndex: 0,
        // }),
        text: create_taxon_text(
            feature.get("sci_name"),
            feature.get("label_font_size"),
            feature.get(selectedLanguage == "fr" ? "common_name_fr" : "common_name_en")
        ),
    });

    return label_style;
};

const labels_source = new Vector();
const labels_layer = new VectorLayer({
    source: labels_source,
    style: label_style_function,
    declutter: true,
    zIndex: 5,
});

function create_taxon_text(taxonName, taxonNameLabelFontSize, taxonCommonName) {
    const taxonNameLabelFont = `${taxonNameLabelFontSize}px Segoe UI, Helvetica, sans-serif`;
    const taxonCommonNameLabelFontSize = taxonNameLabelFontSize - 8;
    const taxonCommonNameLabelFont = `${taxonCommonNameLabelFontSize}px Segoe UI, Helvetica, sans-serif`;
    const nameText = [taxonName, taxonNameLabelFont];
    const commonNameText =
        taxonCommonName && taxonCommonNameLabelFontSize > 10
            ? ["\n", taxonNameLabelFont, taxonCommonName, taxonCommonNameLabelFont]
            : [];
    const text = [...nameText, ...commonNameText];

    const text_style = new Text({
        fill: new Fill({ color: TEXT_COLOR }),
        stroke: new Stroke({ width: 2, color: TEXT_STROKE_COLOR }),
        text: text,
        offsetY: 10,
        textBaseline: "top",
    });

    return text_style;
}

function to_taxon(doc, zoom) {
    console.log(selectedLanguage);
    const common_name_field =
        selectedLanguage == "fr" ? "common_name_fr" : "common_name_en";
    let taxon = {};
    taxon["sci_name"] = doc["sci_name"][0];
    taxon[common_name_field] = doc[common_name_field]
        ? doc[common_name_field][0]
        : undefined;
    taxon["geometry"] = new Point(fromLonLat([doc["lon"], doc["lat"]]));
    taxon["zoom"] = doc["zoom"][0];
    taxon["label_font_size"] = 16 + (zoom - doc["zoom"][0]) * 3;
    return new Feature(taxon);
}

function list_for_extent(zoom, extent) {
    zoom = Math.round(zoom);
    const url = `${API_URL}/taxo/select?q=*:*&fq=zoom:[0 TO ${zoom}]&fq=lat:[${extent[1]} TO ${extent[3]}]&fq=lon:[${extent[0]} TO ${extent[2]}]&wt=json&rows=1000`;
    const list_taxa = () =>
        fetch(url)
            .then((response) => response.json())
            .then((response) => response.response.docs.map((d) => to_taxon(d, zoom)))
            .catch(function (ex) {
                console.warn("parsing failed", ex);
            });

    return list_taxa();
}

async function refresh_labels(map) {
    let extent = map.getView().calculateExtent();
    extent = [...toLonLat(getBottomLeft(extent)), ...toLonLat(getTopRight(extent))];
    const zoom = map.getView().getZoom();
    let labels = await list_for_extent(zoom + 3, extent);
    labels_source.clear();
    labels_source.addFeatures(labels);
    map.render();
}

async function on_move_end(ev) {
    const map = ev.map;
    refresh_labels(map);
}

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

const archae_style = new Style({
    fill: new Fill({ color: "rgba(170, 255, 238, 0.12)" }),
});
const eukaryotes_style = new Style({
    fill: new Fill({ color: "rgba(101, 153, 255, 0.15)" }),
});
const bacteria_style = new Style({
    fill: new Fill({ color: "rgba(255, 128, 128, 0.1)" }),
});

const polygon_layers = new VectorTileLayer({
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
});

const lines_layer = new VectorTileLayer({
    source: new VectorTileSource({
        maxZoom: 42,
        format: new MVT(),
        url: "https://lifemap-back.dev.lhst.eu/vector_tiles/xyz/lines/{z}/{x}/{y}.pbf",
    }),
    style: new Style({ stroke: new Stroke({ color: "#cacaca", whidth: 0.8 }) }),
});

const rank_lines_layer = new VectorTileLayer({
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
});

const rank_text_layer = new VectorTileLayer({
    declutter: true,
    source: new VectorTileSource({
        maxZoom: 42,
        format: new MVT(),
        url: "https://lifemap-back.dev.lhst.eu/vector_tiles/xyz/ranks/{z}/{x}/{y}.pbf",
    }),
    style: function (feature) {
        rankStyle.getText().setText(feature.get("rank_en"));
        // .setText([
        //   ` ${feature.get('rank')}`,
        //   '',
        //   '\n',
        //   '',
        // ]);
        // style.getText().setText(feature.get('name'));

        return style;
    },
});

const leaves_text_layer = new VectorTileLayer({
    declutter: true,
    source: new VectorTileSource({
        maxZoom: 42,
        format: new MVT(),
        url: "https://lifemap-back.dev.lhst.eu/vector_tiles/xyz/leaves/{z}/{x}/{y}.pbf",
    }),
    style: function (feature) {
        leaveStyle.getText().setText([` ${feature.get("sci_name")}`, "", "\n", ""]);
        return style;
    },
});

const clade_text_layer = new VectorTileLayer({
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
                ` ${feature.get("common_name_en")}`,
                "",
            ]);
        return style;
    },
});

const map = new Map({
    target: "map",
    view: new View({
        center: fromLonLat([0, -4.226497]),
        zoom: 5,
        minZoom: 4,
        maxZoom: 42,
        enableRotation: false,
        constrainResolution: true,
        smoothResolutionConstraint: false,
    }),
    layers: [
        polygon_layers,
        lines_layer,
        rank_lines_layer,
        rank_text_layer,
        //leaves_text_layer,
        //clade_text_layer,
        labels_layer,
    ],
});

map.on("moveend", on_move_end);

// language selection
const languageSelect = document.getElementById("lang");
let selectedLanguage = localStorage.getItem("selectedLanguage") || "en";
languageSelect.value = selectedLanguage;
// Listen for changes to the language selection
languageSelect.addEventListener("change", () => {
    selectedLanguage = languageSelect.value;
    localStorage.setItem("selectedLanguage", selectedLanguage);
    refresh_labels(map);
});
