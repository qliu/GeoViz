/*
 * Copyright (C) 2014 United States Government as represented by the Administrator of the
 * National Aeronautics and Space Administration. All Rights Reserved.
 */
/**
 * @exports Texture
 * @version $Id: Texture.js 2941 2015-03-30 21:11:43Z tgaskins $
 */
define([
        '../error/ArgumentError',
        '../util/Logger',
        '../util/WWMath'
    ],
    function (ArgumentError,
              Logger,
              WWMath) {
        "use strict";

        /**
         * Constructs a texture for a specified image.
         * @alias Texture
         * @constructor
         * @classdesc Represents a WebGL texture. Applications typically do not interact with this class.
         * @param {WebGLRenderingContext} gl The current WebGL rendering context.
         * @param {Image} image The texture's image.
         * @throws {ArgumentError} If the specified WebGL context or image is null or undefined.
         */
        var Texture = function (gl, image) {
            if (!gl) {
                throw new ArgumentError(Logger.logMessage(Logger.LEVEL_SEVERE, "Texture", "constructor",
                    "missingGlContext"));
            }

            if (!image) {
                throw new ArgumentError(Logger.logMessage(Logger.LEVEL_SEVERE, "Texture", "constructor",
                    "missingImage"));
            }

            if (Texture.extTextureFilterAnisotropic == undefined) {
                Texture.extTextureFilterAnisotropic = gl.getExtension("EXT_texture_filter_anisotropic");
            }

            var textureId = gl.createTexture(),
                isPowerOfTwo = (WWMath.isPowerOfTwo(image.width) && WWMath.isPowerOfTwo(image.height)),
                extAnisotropic = Texture.extTextureFilterAnisotropic;

            this.imageWidth = image.width;
            this.imageHeight = image.height;
            this.size = image.width * image.height * 4;
            this.originalImageWidth = this.imageWidth;
            this.originalImageHeight = this.imageHeight;

            gl.bindTexture(WebGLRenderingContext.TEXTURE_2D, textureId);
            gl.texParameteri(WebGLRenderingContext.TEXTURE_2D, WebGLRenderingContext.TEXTURE_MIN_FILTER,
                isPowerOfTwo ? WebGLRenderingContext.LINEAR_MIPMAP_LINEAR : WebGLRenderingContext.LINEAR);
            gl.texParameteri(WebGLRenderingContext.TEXTURE_2D, WebGLRenderingContext.TEXTURE_MAG_FILTER,
                WebGLRenderingContext.LINEAR);
            gl.texParameteri(WebGLRenderingContext.TEXTURE_2D, WebGLRenderingContext.TEXTURE_WRAP_S,
                WebGLRenderingContext.CLAMP_TO_EDGE);
            gl.texParameteri(WebGLRenderingContext.TEXTURE_2D, WebGLRenderingContext.TEXTURE_WRAP_T,
                WebGLRenderingContext.CLAMP_TO_EDGE);

            if (extAnisotropic) {
                gl.texParameteri(WebGLRenderingContext.TEXTURE_2D, extAnisotropic.TEXTURE_MAX_ANISOTROPY_EXT, 4);
            }

            gl.pixelStorei(WebGLRenderingContext.UNPACK_PREMULTIPLY_ALPHA_WEBGL, 1);
            gl.texImage2D(WebGLRenderingContext.TEXTURE_2D, 0,
                WebGLRenderingContext.RGBA, WebGLRenderingContext.RGBA, WebGLRenderingContext.UNSIGNED_BYTE, image);
            gl.pixelStorei(WebGLRenderingContext.UNPACK_PREMULTIPLY_ALPHA_WEBGL, 0);

            if (isPowerOfTwo) {
                gl.generateMipmap(WebGLRenderingContext.TEXTURE_2D);
            }

            this.textureId = textureId;
        };

        // Internal use only. Keeps a class level instance to the WebGL EXT_texture_filter_anisotropic interface object.
        // For details on this WebGL extension, see
        // https://www.khronos.org/registry/webgl/extensions/EXT_texture_filter_anisotropic
        Texture.extTextureFilterAnisotropic = undefined;

        /**
         * Disposes of the WebGL texture object associated with this texture.
         * @param gl
         */
        Texture.prototype.dispose = function (gl) {
            gl.deleteTexture(this.textureId);
            delete this.textureId;
        };

        /**
         * Binds this texture in the current WebGL graphics context.
         * @param {DrawContext} dc The current draw context.
         */
        Texture.prototype.bind = function (dc) {
            dc.currentGlContext.bindTexture(WebGLRenderingContext.TEXTURE_2D, this.textureId);
            dc.frameStatistics.incrementTextureLoadCount(1);
            return true;
        };

        return Texture;
    });