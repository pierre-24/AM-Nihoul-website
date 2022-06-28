const output_dir = 'AM_Nihoul_website/static/';
const input_dir = 'AM_Nihoul_website/assets/';

const tasks = [
    'grunt-contrib-jshint',
    'grunt-contrib-less',
    'grunt-contrib-uglify',
    'grunt-contrib-watch',
    'grunt-image'
];

module.exports = function(grunt) {
    grunt.initConfig({
        jshint: {
            files: ['Gruntfile.js', `${input_dir}/*.js`],
            options: {
                jshintrc: true,
            }
        },
        less: {
            build: {
                options: {
                    compress: true
                },
                cwd: input_dir,
                src: [`*.less`],
                expand: true,
                dest: output_dir,
                ext: '.css'
            }
        },
        uglify: {
            build_editor: {
                src: `${input_dir}/editor.js`,
                dest: `${output_dir}/editor.min.js`
            },
            build_other: {
                src: `${input_dir}/html-fix.js`,
                dest: `${output_dir}/scripts.min.js`
            }
        },
        image: {
            build: {
                files: [{
                    expand: true,
                    cwd: `${input_dir}/images`,
                    src: ['*.{png,svg}'],
                    dest: `${output_dir}/images`
                }]
            }
        },
        watch: {
            js: {
                files: ['<%= jshint.files %>'],
                tasks: ['jshint', 'uglify']
            },
            css: {
                files: [`${input_dir}/style.less`],
                tasks: ['less']
            }
        }
    });

    tasks.forEach((task) => {grunt.loadNpmTasks(task); });
    grunt.registerTask('default', ['jshint', 'less', 'uglify', 'image']);
};