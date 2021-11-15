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
const input_dir = 'AM_Nihoul_website/assets/';

const fast = options.has('fast');
if (fast) {
    console.log('no minification will be performed');
}

function css() {
    return gulp.src(input_dir + 'style.less')
        .pipe(less())
        .pipe(gulp_if(!fast, clean_css()))
        .pipe(gulp.dest(output_dir));
}

gulp.task('css', function () {
    return css();
});

function images() {
    return gulp.src(input_dir + 'images/*')
        .pipe(gulp.dest(output_dir + 'images/'));
}

gulp.task('images', function () {
    return images();
});

function js_file(input) {
    return browserify(input_dir + input)
        .bundle()
        .pipe(gulp_if(!fast, minify()))
        .pipe(source(input.replace('.js', '.min.js')))
        .pipe(gulp.dest(output_dir));
}

gulp.task('js_build', function () {
    return js_file('editor.js');
});

function js_lint_file(input) {
    return gulp.src([input_dir + input])
        .pipe(js_lint())
        .pipe(js_lint.reporter('jshint-stylish'))
        .pipe(js_lint.reporter('fail'));
}

gulp.task('js_lint', function () {
    return js_lint_file('editor.js');
});

function watch() {
    gulp.watch([input_dir + 'editor.js'], {}, gulp.series('js'));
    gulp.watch([input_dir + 'style.less'], {}, gulp.series('css'));
    gulp.watch([input_dir + 'images/*'], {}, gulp.series('images'));
}

gulp.task('build', gulp.parallel('css', 'images', 'js_build'));
gulp.task('default', gulp.series('build'));

exports.watch = gulp.series('build', watch);