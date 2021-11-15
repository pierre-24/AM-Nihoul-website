/* ===========================================================
 * trumbowyg.pasteupload.js v1.0
 * Upload pasted images
 * based on the code of pasteimage.js (https://github.com/Alex-D/Trumbowyg/blob/develop/plugins/pasteimage/trumbowyg.pasteimage.js)
 * ===========================================================
 * Author : Pierre Beaujean
 */

(function ($) {
    'use strict';

    let default_options = {
        url: 'null',
        inputField: 'image',
        successField: 'success',
        reasonField: 'reason',
        urlField: 'url'
    }

    $.extend(true, $.trumbowyg, {
        plugins: {
            pasteUpload: {
                init: function (trumbowyg) {

                    // fill default options
                    trumbowyg.o.plugins.pasteUpload = $.extend(true, {},
                        default_options,
                        trumbowyg.o.plugins.pasteUpload || {}
                    );

                    trumbowyg.pasteHandlers.push(function (pasteEvent) {
                        let options = trumbowyg.o.plugins.pasteUpload;
                        try {
                            var items = (pasteEvent.originalEvent || pasteEvent).clipboardData.items,
                                mustPreventDefault = false,
                                reader;

                            for (var i = items.length - 1; i >= 0; i -= 1) {
                                if (items[i].type.match(/^image\//)) {
                                    reader = new FileReader();
                                    /* jshint -W098 */
                                    reader.onloadend = function (event) {
                                        let data = {};
                                        data[options.inputField] = event.target.result;

                                        $.ajax({
                                            type: 'POST',
                                            url: options.url,
                                            data: data,
                                            error: (xhr, status, message) => {
                                                alert(status + '; ' +  message);
                                            },
                                            success: (data, status, xhr) => {
                                                if (data[options.successField])
                                                    trumbowyg.execCmd('insertImage', data[options.urlField], false, true);
                                                else
                                                    alert(data[options.reasonField]);
                                            }
                                        });
                                    };
                                    /* jshint +W098 */
                                    reader.readAsDataURL(items[i].getAsFile());
                                    mustPreventDefault = true;
                                }
                            }
                            if (mustPreventDefault) {
                                pasteEvent.stopPropagation();
                                pasteEvent.preventDefault();
                            }
                        } catch (c) {
                        }
                    });
                },
            }
        }
    });
})(jQuery);