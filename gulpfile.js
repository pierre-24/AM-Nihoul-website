const gulp = require('gulp');
const source = require('vinyl-source-stream');
const browserify = require('browserify');
const minify  = require('minify-stream');
const less = require('gulp-less');
const clean_css = require('gulp-clean-css');
const options = require('gulp-options');
const js_lint = require('gulp-jshint');
const gulp_if = require('gulp-if');

const output_dir = 'AM_Nihoul_website/static/';
const input_dir = 'AM_Nihoul_website/assets/'

const fast = options.has("fast");
if (fast) {
    console.log("no minification will be performed");
}

function js_main() {
    return browserify(input_dir + 'main.js')
        .bundle()
        .pipe(gulp_if(!fast, minify()))
        .pipe(source('main.bundled.js'))
        .pipe(gulp.dest(output_dir))
}

function js_editor() {
    return browserify(input_dir + 'editor.js')
        .bundle()
        .pipe(gulp_if(!fast, minify()))
        .pipe(source('editor.bundled.js'))
        .pipe(gulp.dest(output_dir))
}

function lint() {
    return gulp.src([input_dir + 'main.js'])
        .pipe(js_lint())
        .pipe(js_lint.reporter('jshint-stylish'))
        .pipe(js_lint.reporter('fail'));
}

function css() {
    return gulp.src(input_dir + 'style.less')
        .pipe(less())
        .pipe(gulp_if(!fast, clean_css()))
        .pipe(gulp.dest(output_dir))
}

function images() {
    return gulp.src(input_dir + 'images/*')
        .pipe(gulp.dest(output_dir + 'images/'))
}

gulp.task('lint', function () {
    return lint();
});

gulp.task('js_main', function () {
    return js_main();
});

gulp.task('js_editor', function () {
    return js_editor();
});

gulp.task('css', function () {
    return css();
});



gulp.task('images', function () {
    return images();
});

function watch() {
    gulp.watch([input_dir + 'main.js'], {}, gulp.series('js_main'));
    gulp.watch([input_dir + 'editor.js'], {}, gulp.series('js_editor'));
    gulp.watch([input_dir + 'style.less'], {}, gulp.series('css'));
    gulp.watch([input_dir + 'images/*'], {}, gulp.series('images'));
}

gulp.task('build', gulp.parallel('css', 'images', gulp.series('lint', 'js_main', 'js_editor')));
gulp.task('default', gulp.series('build'));

exports.watch = gulp.series('build', watch);