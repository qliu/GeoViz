/*
 * Copyright (C) 2014 United States Government as represented by the Administrator of the
 * National Aeronautics and Space Administration. All Rights Reserved.
 */
/**
 * @version $Id: WorldWind.js 3054 2015-04-29 19:29:02Z tgaskins $
 */
define([ // PLEASE KEEP ALL THIS IN ALPHABETICAL ORDER BY MODULE NAME (not directory name).
        './error/AbstractError',
        './geom/Angle',
        './error/ArgumentError',
        './shaders/BasicProgram',
        './shaders/BasicTextureProgram',
        './layer/BingAerialLayer',
        './layer/BingAerialWithLabelsLayer',
        './layer/BingRoadsLayer',
        './layer/BingWMSLayer',
        './layer/BMNGLandsatLayer',
        './layer/BMNGLayer',
        './layer/BMNGOneImageLayer',
        './layer/BMNGRestLayer',
        './geom/BoundingBox',
        './util/Color',
        './shapes/Compass',
        './layer/CompassLayer',
        './gesture/DragRecognizer',
        './render/DrawContext',
        './globe/EarthElevationModel',
        './globe/EarthRestElevationModel',
        './globe/ElevationModel',
        './util/Font',
        './util/FrameStatistics',
        './geom/Frustum',
        './projections/GeographicProjection',
        './shapes/GeographicText',
        './gesture/GestureRecognizer',
        './globe/Globe',
        './globe/Globe2D',
        './shaders/GpuProgram',
        './cache/GpuResourceCache',
        './shaders/GpuShader',
        './util/HighlightController',
        './util/ImageSource',
        './render/ImageTile',
        './layer/LandsatRestLayer',
        './layer/Layer',
        './util/Level',
        './util/LevelRowColumnUrlBuilder',
        './util/LevelSet',
        './geom/Line',
        './geom/Location',
        './util/Logger',
        './navigate/LookAtNavigator',
        './geom/Matrix',
        './cache/MemoryCache',
        './cache/MemoryCacheListener',
        './navigate/Navigator',
        './navigate/NavigatorState',
        './error/NotYetImplementedError',
        './util/Offset',
        './gesture/PanRecognizer',
        './shapes/Path',
        './pick/PickedObject',
        './pick/PickedObjectList',
        './gesture/PinchRecognizer',
        './shapes/Placemark',
        './shapes/PlacemarkAttributes',
        './geom/Plane',
        './shapes/Polygon',
        './geom/Position',
        './projections/ProjectionEquirectangular',
        './projections/ProjectionMercator',
        './projections/ProjectionPolarEquidistant',
        './projections/ProjectionUPS',
        './geom/Rectangle',
        './render/Renderable',
        './layer/RenderableLayer',
        './gesture/RotationRecognizer',
        './shapes/ScreenImage',
        './shapes/ScreenText',
        './geom/Sector',
        './shapes/ShapeAttributes',
        './formats/shapefile/Shapefile',
        './layer/ShowTessellationLayer',
        './shapes/SurfaceImage',
        './shapes/SurfaceCircle',
        './shapes/SurfaceEllipse',
        './shapes/SurfacePolygon',
        './shapes/SurfacePolyline',
        './shapes/SurfaceRectangle',
        './shapes/SurfaceSector',
        './shapes/SurfaceShape',
        './shapes/SurfaceShapeTile',
        './shapes/SurfaceShapeTileBuilder',
        './render/SurfaceTile',
        './render/SurfaceTileRenderer',
        './shaders/SurfaceTileRendererProgram',
        './gesture/TapRecognizer',
        './globe/Terrain',
        './globe/TerrainTile',
        './globe/TerrainTileList',
        './globe/Tessellator',
        './shapes/Text',
        './shapes/TextAttributes',
        './render/TextSupport',
        './render/Texture',
        './render/TextureTile',
        './util/Tile',
        './layer/TiledImageLayer',
        './util/TileFactory',
        './gesture/TiltRecognizer',
        './error/UnsupportedOperationError',
        './geom/Vec2',
        './geom/Vec3',
        './layer/ViewControlsLayer',
        './ogc/WmsCapabilities',
        './layer/WmsLayer',
        './ogc/WmsLayerCapabilities',
        './util/WmsUrlBuilder',
        './WorldWindow',
        './util/WWMath',
        './util/WWUtil',
        './globe/ZeroElevationModel'],
    function (AbstractError,
              Angle,
              ArgumentError,
              BasicProgram,
              BasicTextureProgram,
              BingAerialLayer,
              BingAerialWithLabelsLayer,
              BingRoadsLayer,
              BingWMSLayer,
              BMNGLandsatLayer,
              BMNGLayer,
              BMNGOneImageLayer,
              BMNGRestLayer,
              BoundingBox,
              Color,
              Compass,
              CompassLayer,
              DragRecognizer,
              DrawContext,
              EarthElevationModel,
              EarthRestElevationModel,
              ElevationModel,
              Font,
              FrameStatistics,
              Frustum,
              GeographicProjection,
              GeographicText,
              GestureRecognizer,
              Globe,
              Globe2D,
              GpuProgram,
              GpuResourceCache,
              GpuShader,
              HighlightController,
              ImageSource,
              ImageTile,
              LandsatRestLayer,
              Layer,
              Level,
              LevelRowColumnUrlBuilder,
              LevelSet,
              Line,
              Location,
              Logger,
              LookAtNavigator,
              Matrix,
              MemoryCache,
              MemoryCacheListener,
              Navigator,
              NavigatorState,
              NotYetImplementedError,
              Offset,
              PanRecognizer,
              Path,
              PickedObject,
              PickedObjectList,
              PinchRecognizer,
              Placemark,
              PlacemarkAttributes,
              Plane,
              Polygon,
              Position,
              ProjectionEquirectangular,
              ProjectionMercator,
              ProjectionPolarEquidistant,
              ProjectionUPS,
              Rectangle,
              Renderable,
              RenderableLayer,
              RotationRecognizer,
              ScreenImage,
              ScreenText,
              Sector,
              ShapeAttributes,
              Shapefile,
              ShowTessellationLayer,
              SurfaceImage,
              SurfaceCircle,
              SurfaceEllipse,
              SurfacePolygon,
              SurfacePolyline,
              SurfaceRectangle,
              SurfaceSector,
              SurfaceShape,
              SurfaceShapeTile,
              SurfaceShapeTileBuilder,
              SurfaceTile,
              SurfaceTileRenderer,
              SurfaceTileRendererProgram,
              TapRecognizer,
              Terrain,
              TerrainTile,
              TerrainTileList,
              Tessellator,
              Text,
              TextAttributes,
              TextSupport,
              Texture,
              TextureTile,
              Tile,
              TiledImageLayer,
              TileFactory,
              TiltRecognizer,
              UnsupportedOperationError,
              Vec2,
              Vec3,
              ViewControlsLayer,
              WmsCapabilities,
              WmsLayer,
              WmsLayerCapabilities,
              WmsUrlBuilder,
              WorldWindow,
              WWMath,
              WWUtil,
              ZeroElevationModel) {
        "use strict";
        /**
         * This is the top-level World Wind module. It is global.
         * @exports WorldWind
         * @global
         */
        var WorldWind = {
            /**
             * The World Wind version number.
             * @default "0.0.0"
             * @constant
             */
            VERSION: "0.0.0",

            // PLEASE KEEP THE ENTRIES BELOW IN ALPHABETICAL ORDER
            /**
             * Indicates an altitude mode relative to the globe's ellipsoid.
             * @constant
             */
            ABSOLUTE: "absolute",

            /**
             * The BEGAN gesture recognizer state. Continuous gesture recognizers transition to this state from the
             * POSSIBLE state when the gesture is first recognized.
             * @constant
             */
            BEGAN: "began",

            /**
             * The CANCELLED gesture recognizer state. Continuous gesture recognizers may transition to this state from
             * the BEGAN state or the CHANGED state when the touch events are cancelled.
             * @constant
             */
            CANCELLED: "cancelled",

            /**
             * The CHANGED gesture recognizer state. Continuous gesture recognizers transition to this state from the
             * BEGAN state or the CHANGED state, whenever an input event indicates a change in the gesture.
             * @constant
             */
            CHANGED: "changed",

            /**
             * Indicates an altitude mode always on the terrain.
             * @constant
             */
            CLAMP_TO_GROUND: "clampToGround",

            /**
             * The radius of Earth.
             * @constant
             */
            EARTH_RADIUS: 6371e3,

            /**
             * Indicates the cardinal direction east.
             * @constant
             */
            EAST: "east",

            /**
             * The ENDED gesture recognizer state. Continuous gesture recognizers transition to this state from either
             * the BEGAN state or the CHANGED state when the current input no longer represents the gesture.
             * @constant
             */
            ENDED: "ended",

            /**
             * The FAILED gesture recognizer state. Gesture recognizers transition to this state from the POSSIBLE state
             * when the gesture cannot be recognized given the current input.
             * @constant
             */
            FAILED: "failed",

            /**
             * Indicates a great circle path.
             * @constant
             */
            GREAT_CIRCLE: "greatCircle",

            /**
             * Indicates a linear, straight line path.
             * @constant
             */
            LINEAR: "linear",

            /**
             * Indicates a multi-point shape, typically within a shapefile.
             */
            MULTI_POINT: "multiPoint",

            /**
             * Indicates the cardinal direction north.
             * @constant
             */
            NORTH: "north",

            /**
             * Indicates a null shape, typically within a shapefile.
             * @constant
             */
            NULL: "null",

            /**
             * Indicates that the associated parameters are fractional values of the virtual rectangle's width or
             * height in the range [0, 1], where 0 indicates the rectangle's origin and 1 indicates the corner
             * opposite its origin.
             * @constant
             */
            OFFSET_FRACTION: "fraction",

            /**
             * Indicates that the associated parameters are in units of pixels relative to the virtual rectangle's
             * corner opposite its origin corner.
             * @constant
             */
            OFFSET_INSET_PIXELS: "insetPixels",

            /**
             * Indicates that the associated parameters are in units of pixels relative to the virtual rectangle's
             * origin.
             * @constant
             */
            OFFSET_PIXELS: "pixels",

            /**
             * Indicates a point shape, typically within a shapefile.
             */
            POINT: "point",

            /**
             * Indicates a polyline shape, typically within a shapefile.
             */
            POLYLINE: "polyline",

            /**
             * Indicates a polygon shape, typically within a shapefile.
             */
            POLYGON: "polygon",

            /**
             * The POSSIBLE gesture recognizer state. Gesture recognizers in this state are idle when there is no input
             * event to evaluate, or are evaluating input events to determine whether or not to transition into another
             * state.
             * @constant
             */
            POSSIBLE: "possible",

            /**
             * The RECOGNIZED gesture recognizer state. Discrete gesture recognizers transition to this state from the
             * POSSIBLE state when the gesture is recognized.
             * @constant
             */
            RECOGNIZED: "recognized",

            /**
             * The event name of World Wind redraw events.
             */
            REDRAW_EVENT_TYPE: "WorldWindRedraw",

            /**
             * Indicates an altitude mode relative to the terrain.
             * @constant
             */
            RELATIVE_TO_GROUND: "relativeToGround",

            /**
             * Indicates a rhumb path -- a path of constant bearing.
             * @constant
             */
            RHUMB_LINE: "rhumbLine",

            /**
             * Indicates the cardinal direction south.
             * @constant
             */
            SOUTH: "south",

            /**
             * Indicates the cardinal direction west.
             * @constant
             */
            WEST: "west"
        };

        WorldWind['AbstractError'] = AbstractError;
        WorldWind['Angle'] = Angle;
        WorldWind['ArgumentError'] = ArgumentError;
        WorldWind['BasicProgram'] = BasicProgram;
        WorldWind['BasicTextureProgram'] = BasicTextureProgram;
        WorldWind['BingAerialLayer'] = BingAerialLayer;
        WorldWind['BingAerialWithLabelsLayer'] = BingAerialWithLabelsLayer;
        WorldWind['BingRoadsLayer'] = BingRoadsLayer;
        WorldWind['BingWMSLayer'] = BingWMSLayer;
        WorldWind['BMNGLandsatLayer'] = BMNGLandsatLayer;
        WorldWind['BMNGLayer'] = BMNGLayer;
        WorldWind['BMNGOneImageLayer'] = BMNGOneImageLayer;
        WorldWind['BMNGRestLayer'] = BMNGRestLayer;
        WorldWind['BoundingBox'] = BoundingBox;
        WorldWind['Color'] = Color;
        WorldWind['Compass'] = Compass;
        WorldWind['CompassLayer'] = CompassLayer;
        WorldWind['DragRecognizer'] = DragRecognizer;
        WorldWind['DrawContext'] = DrawContext;
        WorldWind['EarthElevationModel'] = EarthElevationModel;
        WorldWind['EarthRestElevationModel'] = EarthRestElevationModel;
        WorldWind['ElevationModel'] = ElevationModel;
        WorldWind['Font'] = Font;
        WorldWind['FrameStatistics'] = FrameStatistics;
        WorldWind['Frustum'] = Frustum;
        WorldWind['GeographicProjection'] = GeographicProjection;
        WorldWind['GeographicText'] = GeographicText;
        WorldWind['GestureRecognizer'] = GestureRecognizer;
        WorldWind['Globe'] = Globe;
        WorldWind['Globe2D'] = Globe2D;
        WorldWind['GpuProgram'] = GpuProgram;
        WorldWind['GpuResourceCache'] = GpuResourceCache;
        WorldWind['GpuShader'] = GpuShader;
        WorldWind['HighlightController'] = HighlightController;
        WorldWind['ImageSource'] = ImageSource;
        WorldWind['ImageTile'] = ImageTile;
        WorldWind['LandsatRestLayer'] = LandsatRestLayer;
        WorldWind['Layer'] = Layer;
        WorldWind['Level'] = Level;
        WorldWind['LevelRowColumnUrlBuilder'] = LevelRowColumnUrlBuilder;
        WorldWind['LevelSet'] = LevelSet;
        WorldWind['Line'] = Line;
        WorldWind['Location'] = Location;
        WorldWind['Logger'] = Logger;
        WorldWind['LookAtNavigator'] = LookAtNavigator;
        WorldWind['Matrix'] = Matrix;
        WorldWind['MemoryCache'] = MemoryCache;
        WorldWind['MemoryCacheListener'] = MemoryCacheListener;
        WorldWind['Navigator'] = Navigator;
        WorldWind['NavigatorState'] = NavigatorState;
        WorldWind['NotYetImplementedError'] = NotYetImplementedError;
        WorldWind['Offset'] = Offset;
        WorldWind['PanRecognizer'] = PanRecognizer;
        WorldWind['Path'] = Path;
        WorldWind['PickedObject'] = PickedObject;
        WorldWind['PickedObjectList'] = PickedObjectList;
        WorldWind['PinchRecognizer'] = PinchRecognizer;
        WorldWind['Placemark'] = Placemark;
        WorldWind['PlacemarkAttributes'] = PlacemarkAttributes;
        WorldWind['Plane'] = Plane;
        WorldWind['Polygon'] = Polygon;
        WorldWind['Position'] = Position;
        WorldWind['ProjectionEquirectangular'] = ProjectionEquirectangular;
        WorldWind['ProjectionMercator'] = ProjectionMercator;
        WorldWind['ProjectionPolarEquidistant'] = ProjectionPolarEquidistant;
        WorldWind['ProjectionUPS'] = ProjectionUPS;
        WorldWind['Rectangle'] = Rectangle;
        WorldWind['Renderable'] = Renderable;
        WorldWind['RenderableLayer'] = RenderableLayer;
        WorldWind['RotationRecognizer'] = RotationRecognizer;
        WorldWind['ScreenText'] = ScreenText;
        WorldWind['ScreenImage'] = ScreenImage;
        WorldWind['Sector'] = Sector;
        WorldWind['ShapeAttributes'] = ShapeAttributes;
        WorldWind['Shapefile'] = Shapefile;
        WorldWind['ShowTessellationLayer'] = ShowTessellationLayer;
        WorldWind['SurfaceImage'] = SurfaceImage;
        WorldWind['SurfaceCircle'] = SurfaceCircle;
        WorldWind['SurfaceEllipse'] = SurfaceEllipse;
        WorldWind['SurfacePolygon'] = SurfacePolygon;
        WorldWind['SurfacePolyline'] = SurfacePolyline;
        WorldWind['SurfaceRectangle'] = SurfaceRectangle;
        WorldWind['SurfaceSector'] = SurfaceSector;
        WorldWind['SurfaceShape'] = SurfaceShape;
        WorldWind['SurfaceShapeTile'] = SurfaceShapeTile;
        WorldWind['SurfaceShapeTileBuilder'] = SurfaceShapeTileBuilder;
        WorldWind['SurfaceTile'] = SurfaceTile;
        WorldWind['SurfaceTileRenderer'] = SurfaceTileRenderer;
        WorldWind['SurfaceTileRendererProgram'] = SurfaceTileRendererProgram;
        WorldWind['TapRecognizer'] = TapRecognizer;
        WorldWind['Terrain'] = Terrain;
        WorldWind['TerrainTile'] = TerrainTile;
        WorldWind['TerrainTileList'] = TerrainTileList;
        WorldWind['Tessellator'] = Tessellator;
        WorldWind['Text'] = Text;
        WorldWind['TextAttributes'] = TextAttributes;
        WorldWind['TextSupport'] = TextSupport;
        WorldWind['Texture'] = Texture;
        WorldWind['TextureTile'] = TextureTile;
        WorldWind['Tile'] = Tile;
        WorldWind['TiledImageLayer'] = TiledImageLayer;
        WorldWind['TileFactory'] = TileFactory;
        WorldWind['TiltRecognizer'] = TiltRecognizer;
        WorldWind['UnsupportedOperationError'] = UnsupportedOperationError;
        WorldWind['Vec2'] = Vec2;
        WorldWind['Vec3'] = Vec3;
        WorldWind['ViewControlsLayer'] = ViewControlsLayer;
        WorldWind['WmsCapabilities'] = WmsCapabilities;
        WorldWind['WmsLayer'] = WmsLayer;
        WorldWind['WmsLayerCapabilities'] = WmsLayerCapabilities;
        WorldWind['WmsUrlBuilder'] = WmsUrlBuilder;
        WorldWind['WWMath'] = WWMath;
        WorldWind['WWUtil'] = WWUtil;
        WorldWind['WorldWindow'] = WorldWindow;
        WorldWind['ZeroElevationModel'] = ZeroElevationModel;

        /**
         * Holds configuration parameters for World Wind. Applications may modify these parameters prior to creating
         * their first World Wind objects. Configuration properties are:
         * <ul>
         *     <li><code>gpuCacheSize</code>: A Number indicating the size in bytes to allocate from GPU memory for
         *     resources such as textures, GLSL programs and buffer objects. Default is 250e6 (250 MB).
         * </ul>
         * @type {{gpuCacheSize: number}}
         */
        WorldWind.configuration = {
            gpuCacheSize: 250e6
        };

        /**
         * Indicates the Bing Maps key to use when requesting Bing Maps resources.
         * @type {String}
         * @default null
         */
        WorldWind.BingMapsKey = null;

        window.WorldWind = WorldWind;

        return WorldWind;
    }
)
;