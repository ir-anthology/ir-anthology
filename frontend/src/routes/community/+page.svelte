<script lang="ts">
    const sections: { title: string; description: string; items: { label: string; href: string }[] }[] = [
        {
            title: 'Societies',
            description: 'Professional associations and special interest groups in information retrieval.',
            items: [
                { label: 'ACM SIGIR', href: 'https://sigir.org/' },
                { label: 'ACM SIGIR Tokyo', href: 'https://sigir.jp/' },
                { label: 'ARIA', href: 'http://www.asso-aria.org/' },
                { label: 'ASIS&T', href: 'https://www.asist.org/' },
                { label: 'BCS IRSG', href: 'https://irsg.bcs.org/' },
                { label: 'CLEF Initiative', href: 'http://www.clef-initiative.eu/' },
                { label: 'GI FGIR', href: 'https://fg-retrieval.gi.de/' },
                { label: 'HTAi', href: 'https://htai.org/interest-groups/information-retrieval/' },
                { label: 'IRSI', href: 'http://irsi.res.in/' },
                { label: 'ISMIR', href: 'https://www.ismir.net/' },
                { label: 'MIR (archived)', href: 'https://web.archive.org/web/20160406110537/http://www.mirsociety.org/home/visitorpage.php' },
                { label: 'PECAMP', href: 'https://pecamp.org/' },
                { label: 'ROMIP', href: 'http://romip.ru/' },
                { label: 'WGI', href: 'https://www.informatiewetenschap.org/' },
            ]
        },
        {
            title: 'Schools',
            description: 'Summer and autumn schools for aspiring IR researchers.',
            items: [
                { label: 'ASIRF', href: 'https://www.dagstuhl.de/en/program/calendar/?catchword=autumn%20school' },
                { label: 'EARIA', href: 'http://www.asso-aria.org/earia/' },
                { label: 'ESSIR', href: 'http://ims.dei.unipd.it/websites/essir/home.html' },
                { label: 'RUSSIR', href: 'http://russir.org/' },
            ]
        },
        {
            title: 'Retreats',
            description: 'Community retreats and invitational workshops.',
            items: [
                { label: 'HIPstIR', href: 'https://bmitra-msft.github.io/HIPstIR/' },
                { label: 'NSF-sponsored workshop on Task-Based Information Search', href: 'https://ils.unc.edu/taskbasedsearch/index.html' },
            ]
        },
        {
            title: 'Social Media',
            description: 'Mailing lists, newsletters, and online communities.',
            items: [
                { label: 'SIG-IRList', href: 'https://sigir.org/sig-irlist/' },
                { label: 'JISC', href: 'https://www.jiscmail.ac.uk/' },
                { label: 'CLEF', href: 'https://list.uva.nl/mailman/listinfo/clef' },
                { label: 'NTCIR', href: 'https://research.nii.ac.jp/ntcir/ml-en.html' },
                { label: 'r/informationretrieval', href: 'https://www.reddit.com/r/informationretrieval/' },
                { label: 'r/musicir', href: 'https://www.reddit.com/r/musicir/' },
            ]
        },
        {
            title: 'Teaching Material',
            description: 'Lectures and other material for teaching information retrieval.',
            items: [
                { label: 'Video (IR Anthology)', href: 'https://www.youtube.com/channel/UCHkakd2tViHmUxtFgMw4f7g' },
            ]
        },
    ];
</script>

<svelte:head>
    <title>Community – IR Anthology</title>
</svelte:head>

<div class="max-w-3xl">
    <h1 class="text-3xl font-bold mb-2">Community</h1>
    <p class="text-gray-600 mb-4">
        Societies, schools, retreats, and other resources from the information retrieval community.
    </p>

    <hr class="mb-8">

    {#each sections as section (section.title)}
        <section class="mb-8">
            <h2 class="text-xl font-semibold mb-1">{section.title}</h2>
            <p class="text-sm text-gray-500 mb-3">{section.description}</p>
            <ul class="flex flex-wrap gap-x-6 gap-y-2">
                {#each section.items as item (item.label)}
                    <li>
                        <!-- eslint-disable-next-line svelte/no-navigation-without-resolve -- external URLs, not app routes -->
                        <a href={item.href} target="_blank" rel="noopener noreferrer" class="link">
                            {item.label}<span class="text-gray-400 text-xs align-super ml-0.5">&nearr;</span>
                        </a>
                    </li>
                {/each}
            </ul>
        </section>
    {/each}
</div>
