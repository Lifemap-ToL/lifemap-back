import "./style.css";
import MVT from "ol/format/MVT.js";
import Map from "ol/Map.js";
import VectorTileLayer from "ol/layer/VectorTile.js";
import VectorTileSource from "ol/source/VectorTile.js";
import View from "ol/View.js";
import { Fill, Stroke, Style, Text, Circle } from "ol/style.js";
import { Vector } from "ol/source.js";
import VectorLayer from "ol/layer/Vector.js";
import { fromLonLat, toLonLat } from "ol/proj";
import Feature from "ol/Feature.js";
import Point from "ol/geom/Point.js";
import { boundingExtent, getBottomLeft, getTopRight } from "ol/extent.js";
import { MouseWheelZoom, defaults } from "ol/interaction.js";
import { BACKEND_HOSTNAME } from "./backend_hostname";

const SOLR_API_URL = BACKEND_HOSTNAME + "/solr";

// --- THEMES DEFINITION ---

const DARK_THEME = {
    background_color: "#000",
    label_text_color: "rgba(255, 255, 255, 1)",
    label_stroke_color: "rgba(0, 0, 0, 1)",
    circle_fill_color: "rgba(225, 87, 89, 1)",
    circle_stroke_color: "#000",
    archae_fill_color: [170, 255, 238, 0.2],
    eukaryotes_fill_color: [101, 153, 255, 0.23],
    bacteria_fill_color: [255, 128, 128, 0.18],
    archae_rank_color: "#aaffee48",
    eukaryotes_rank_color: "#6599ff55",
    bacteria_rank_color: "#ff808043",
    branches_stroke_color: "#cacaca",
    branches_width: 0.8,
};

const LIGHT_THEME = {
    background_color: "#FFF",
    label_text_color: "rgba(0, 0, 0, 1)",
    label_stroke_color: "rgba(255, 255, 255, 1)",
    circle_fill_color: "rgba(225, 87, 89, 1)",
    circle_stroke_color: "#FFF",
    archae_fill_color: [170, 235, 208, 0.32],
    eukaryotes_fill_color: [101, 153, 255, 0.35],
    bacteria_fill_color: [255, 128, 128, 0.3],
    archae_rank_color: "#aaddeef0",
    eukaryotes_rank_color: "#6599ffe0",
    bacteria_rank_color: "#ff8080e0",
    branches_stroke_color: "#555",
    branches_width: 0.8,
};

let theme = DARK_THEME;

// --- LABELS FUNCTIONS ---

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
        fill: new Fill({ color: theme["label_text_color"] }),
        stroke: new Stroke({ width: 2, color: theme["label_stroke_color"] }),
        text: text,
        offsetY: 10,
        textBaseline: "top",
    });

    return text_style;
}

function to_taxon(doc, zoom) {
    const common_name_field = "common_name_" + selectedLanguage;
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
    const url = `${SOLR_API_URL}/taxo/select?q=*:*&fq=zoom:[0 TO ${zoom}]&fq=lat:[${extent[1]} TO ${extent[3]}]&fq=lon:[${extent[0]} TO ${extent[2]}]&wt=json&rows=1000`;
    const list_taxa = () =>
        fetch(url)
            .then((response) => response.json())
            .then((response) => response.response.docs.map((d) => to_taxon(d, zoom)))
            .catch(function (ex) {
                console.warn("parsing failed", ex);
            });

    return list_taxa();
}

// --- STYLES ---

function labels_style() {
    return (feature) => {
        return new Style({
            image: new Circle({
                radius: 4,
                fill: new Fill({ color: theme["circle_fill_color"] }),
                stroke: new Stroke({
                    width: 1,
                    color: theme["circle_stroke_color"],
                }),
                declutterMode: "none",
                zIndex: 0,
            }),
            text: create_taxon_text(
                feature.get("sci_name"),
                feature.get("label_font_size"),
                feature.get(
                    selectedLanguage == "fr" ? "common_name_fr" : "common_name_en"
                )
            ),
        });
    };
}

function polygons_style() {
    return function (feature) {
        const prop = feature.getProperties();
        const ref = prop.ref;
        const themeColor =
            ref == 1
                ? theme["archae_fill_color"]
                : ref == 2
                ? theme["eukaryotes_fill_color"]
                : theme["bacteria_fill_color"];
        const currentZoom = map.getView().getZoom();
        const zoomLevel = feature.get("zoomview");
        const opacityFactor =
            currentZoom !== undefined ? 1 - Math.abs(currentZoom - zoomLevel - 1) / 5 : 1;
        const fillColor = [
            themeColor[0],
            themeColor[1],
            themeColor[2],
            themeColor[3] * opacityFactor,
        ];
        return new Style({
            fill: new Fill({ color: fillColor }),
            zIndex: 0,
        });
    };
}

function branches_style() {
    return new Style({
        stroke: new Stroke({
            color: theme["branches_stroke_color"],
            width: theme["branches_width"],
        }),
        zIndex: 6,
    });
}

function ranks_style() {
    return function (feature) {
        const prop = feature.getProperties();
        const ref = prop.ref;
        const convex = prop.convex;
        // TODO: fix this ugly hack to avoid rank repeat
        const label =
            "            " + prop[`rank_${selectedLanguage}`] + "              ";
        const text_color =
            ref == 1
                ? theme["archae_rank_color"]
                : ref == 2
                ? theme["eukaryotes_rank_color"]
                : theme["bacteria_rank_color"];
        let style = new Style({
            text: new Text({
                font: 'bold 11px "Open Sans", "Roboto", "Arial Unicode MS", "Arial", "sans-serif"',
                placement: "line",
                overflow: true,
                repeat: 2000,
                padding: [0, 2000, 0, 2000],
                textBaseline: convex < 0 ? "top" : "bottom",
                offsetY: convex < 0 ? -15 : 15,
                fill: new Fill({
                    color: text_color,
                }),
                zIndex: 5,
                text: label,
                declutterMode: "declutter",
            }),
        });
        return style;
    };
}

function composite_style() {
    const poly_style = polygons_style();
    const branch_style = branches_style();
    const rank_style = ranks_style();

    return function (feature) {
        const type = feature.getProperties()["layer"];
        return type == "poly-layer"
            ? poly_style(feature)
            : type == "branches-layer"
            ? branch_style
            : rank_style(feature);
    };
}

// --- LAYERS ---

const composite_layer = new VectorTileLayer({
    name: "composite",
    background: theme["background_color"],
    source: new VectorTileSource({
        maxZoom: 42,
        format: new MVT(),
        url: BACKEND_HOSTNAME + "/vector_tiles/xyz/composite/{z}/{x}/{y}.pbf",
        transition: 100,
    }),
    style: composite_style(),
    declutter: true,
    renderMode: "vector",
    updateWhileAnimating: true,
    updateWhileInteracting: true,
    renderBuffer: 256,
    preload: Infinity,
});

const polygons_layer = new VectorTileLayer({
    name: "polygons",
    background: theme["background_color"],
    source: new VectorTileSource({
        maxZoom: 42,
        format: new MVT(),
        url: BACKEND_HOSTNAME + "/vector_tiles/xyz/composite/{z}/{x}/{y}.pbf",
        transition: 500,
    }),
    style: polygons_style(),
    declutter: false,
    renderMode: "vector",
    updateWhileAnimating: true,
    updateWhileInteracting: true,
    renderBuffer: 256,
    preload: Infinity,
});

const branches_layer = new VectorTileLayer({
    name: "branches",
    source: new VectorTileSource({
        maxZoom: 42,
        format: new MVT(),
        url: BACKEND_HOSTNAME + "/vector_tiles/xyz/composite/{z}/{x}/{y}.pbf",
    }),
    style: branches_style(),
    declutter: true,
    renderMode: "vector",
    updateWhileAnimating: true,
    updateWhileInteracting: true,
    renderBuffer: 256,
    preload: Infinity,
});

const ranks_layer = new VectorTileLayer({
    name: "ranks",
    source: new VectorTileSource({
        maxZoom: 42,
        format: new MVT(),
        url: BACKEND_HOSTNAME + "/vector_tiles/xyz/composite/{z}/{x}/{y}.pbf",
    }),
    style: ranks_style(),
    declutter: true,
    renderMode: "vector",
    updateWhileAnimating: true,
    updateWhileInteracting: true,
    renderBuffer: 256,
    preload: Infinity,
});

const labels_source = new Vector();
const labels_layer = new VectorLayer({
    source: labels_source,
    style: labels_style(),
    declutter: true,
    zIndex: 5,
});

// --- MAP ---

const map = new Map({
    target: "map",
    view: new View({
        center: fromLonLat([0, -4.226497]),
        extent: boundingExtent([fromLonLat([-70, -60]), fromLonLat([70, 50])]),
        zoom: 5,
        minZoom: 4,
        maxZoom: 42,
        enableRotation: false,
        constrainResolution: false,
        smoothResolutionConstraint: false,
    }),
    layers: [composite_layer, labels_layer],
    interactions: defaults().extend([
        new MouseWheelZoom({
            onFocusOnly: false,
            constrainResolution: false,
            maxDelta: 1,
            duration: 300,
            timeout: 100,
        }),
    ]),
});

async function refresh_labels(map) {
    let extent = map.getView().calculateExtent();
    extent = [...toLonLat(getBottomLeft(extent)), ...toLonLat(getTopRight(extent))];
    const zoom = map.getView().getZoom();
    let labels = await list_for_extent(zoom + 3, extent);
    labels_source.clear();
    labels_source.addFeatures(labels);
    map.renderSync();
}

async function on_move_end(ev) {
    const map = ev.map;
    refresh_labels(map);
}

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
    // Refresh rank names
    map.getLayers().item(0).getSource().refresh();
});

// theme selection
const themeSelect = document.getElementById("theme");
let selectedTheme = localStorage.getItem("selectedTheme") || "dark";
themeSelect.value = selectedTheme;
// Listen for changes to the theme selection
themeSelect.addEventListener("change", () => {
    selectedTheme = themeSelect.value;
    localStorage.setItem("selectedtheme", selectedTheme);
    if (selectedTheme == "dark") {
        theme = DARK_THEME;
    }
    if (selectedTheme == "light") {
        theme = LIGHT_THEME;
    }
    // Refresh layers
    map.getLayers().forEach((l) => {
        if (l == composite_layer) {
            l.setBackground(theme["background_color"]);
            l.setStyle(composite_style());
        }
        if (l == polygons_layer) {
            l.setBackground(theme["background_color"]);
            l.setStyle(polygons_style());
        }
        if (l == branches_layer) {
            l.setStyle(branches_style());
        }
        if (l == ranks_layer) {
            l.setStyle(ranks_style());
        }
        if (l == labels_layer) {
            l.setStyle(labels_style());
        }
    });
    map.render();
});
