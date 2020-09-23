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

gulp.task('css', function () {
    return css();
});

gulp.task('images', function () {
    return images();
});

function watch() {
    gulp.watch([input_dir + 'style.less'], {}, gulp.series('css'));
    gulp.watch([input_dir + 'images/*'], {}, gulp.series('images'));
}

gulp.task('build', gulp.parallel('css', 'images'));
gulp.task('default', gulp.series('build'));

exports.watch = gulp.series('build', watch);