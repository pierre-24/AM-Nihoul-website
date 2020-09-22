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

function js_editor() {
    return browserify(input_dir + 'editor.js')
        .bundle()
        .pipe(gulp_if(!fast, minify()))
        .pipe(source('editor.bundled.js'))
        .pipe(gulp.dest(output_dir))
}

function css2() {
    return gulp.src(input_dir + 'style2.less')
        .pipe(less())
        .pipe(gulp_if(!fast, clean_css()))
        .pipe(gulp.dest(output_dir))
}

function images() {
    return gulp.src(input_dir + 'images/*')
        .pipe(gulp.dest(output_dir + 'images/'))
}

gulp.task('js_editor', function () {
    return js_editor();
});

gulp.task('css2', function () {
    return css2();
});

gulp.task('images', function () {
    return images();
});

function watch() {
    gulp.watch([input_dir + 'editor.js'], {}, gulp.series('js_editor'));
    gulp.watch([input_dir + 'style2.less'], {}, gulp.series('css'));
    gulp.watch([input_dir + 'images/*'], {}, gulp.series('images'));
}

gulp.task('build', gulp.parallel('css2', 'images', 'js_editor'));
gulp.task('default', gulp.series('build'));

exports.watch = gulp.series('build', watch);