<script lang="ts">
    const sections: { title: string; items: { label: string; href: string }[] }[] = [
        {
            title: 'Retreats',
            items: [
                { label: "HIPstIR", href: 'https://bmitra-msft.github.io/HIPstIR/' },
                { label: "NSF-sponsored workshop on Task-Based Information Search", href: 'https://ils.unc.edu/taskbasedsearch/index.html' },
            ]
        },
        {
            title: 'Societies',
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
            items: [
                { label: 'ASIRF', href: 'https://www.dagstuhl.de/en/program/calendar/?catchword=autumn%20school' },
                { label: 'EARIA', href: 'http://www.asso-aria.org/earia/' },
                { label: 'ESSIR', href: 'http://ims.dei.unipd.it/websites/essir/home.html' },
                { label: 'RUSSIR', href: 'http://russir.org/' },
            ]
        },
        {
            title: 'Social Media',
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
            items: [
                { label: "Video (IR Anthology)", href: 'https://www.youtube.com/channel/UCHkakd2tViHmUxtFgMw4f7g' },
            ]
        },
        
    ];
</script>

<div class="max-w-3xl mx-auto">
    <h1 class="text-2xl mb-4">Extra</h1>

    {#each sections as section (section.title)}
        <h2 class="text-xl font-semibold mb-2">{section.title}</h2>
        <ul class="list-disc list-inside mb-6 space-y-1">
            {#each section.items as item (item.label)}
                <!-- eslint-disable-next-line svelte/no-navigation-without-resolve -- external URLs, not app routes -->
                <li><a href={item.href} class="link">{item.label}</a></li>
            {/each}
        </ul>
    {/each}
</div>
